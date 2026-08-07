# -*- coding: utf-8 -*-
"""
安全模块 — 速率限制 + 输入校验
支持内存 / Redis 双后端（通过 RATE_LIMIT_BACKEND 环境变量切换）
"""
import time
import json
import re
import hashlib
import os
from abc import ABC, abstractmethod
from functools import wraps
from flask import request, jsonify

# ============================================================
# 可信代理校验（防 X-Forwarded-For 伪造）
# ============================================================

def _is_trusted_proxy(remote_addr: str) -> bool:
    """检查请求来源是否为可信代理"""
    if not remote_addr:
        return False
    from config import TRUSTED_PROXIES
    for proxy in TRUSTED_PROXIES:
        if "/" in proxy:
            # CIDR 格式暂不支持，精确匹配
            if remote_addr == proxy.split("/")[0]:
                return True
        elif remote_addr == proxy:
            return True
    return False


def _get_client_ip() -> str:
    """获取真实客户端 IP（优先从可信代理提供的头部读取）"""
    remote = request.remote_addr or "unknown"

    x_forwarded_for = request.headers.get("X-Forwarded-For", "")
    x_real_ip = request.headers.get("X-Real-IP", "")

    if _is_trusted_proxy(remote):
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        if x_real_ip:
            return x_real_ip.strip()

    return remote


# ============================================================
# RateLimitStore 抽象层
# ============================================================

class RateLimitStore(ABC):
    @abstractmethod
    def get(self, key: str) -> tuple | None:
        """返回 (count, start_time, window) 或 None"""
        ...

    @abstractmethod
    def set(self, key: str, value: tuple):
        ...

    @abstractmethod
    def cleanup(self):
        ...


class MemoryRateLimitStore(RateLimitStore):
    """内存版（默认，但不适合多 worker 部署）"""
    def __init__(self, max_entries: int = 10000):
        self._store = {}
        self._max_entries = max_entries

    def get(self, key: str) -> tuple | None:
        return self._store.get(key)

    def set(self, key: str, value: tuple):
        if len(self._store) > self._max_entries:
            self.cleanup()
        self._store[key] = value

    def cleanup(self):
        now = time.time()
        expired = [k for k, v in self._store.items() if v[0] + v[1] < now]
        for k in expired:
            del self._store[k]


class RedisRateLimitStore(RateLimitStore):
    """Redis 分布式限流存储（适用于多 worker gunicorn 部署）"""
    def __init__(self, redis_url=None):
        self._redis = None
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")

    def _connect(self):
        if self._redis is None:
            try:
                import redis
                self._redis = redis.from_url(self._redis_url, socket_connect_timeout=2)
                self._redis.ping()
            except Exception as e:
                raise RuntimeError(f"Redis 连接失败 ({self._redis_url}): {e}")

    def get(self, key: str) -> tuple | None:
        try:
            self._connect()
            data = self._redis.get(key)
            if data:
                return tuple(json.loads(data))
        except Exception:
            pass
        return None

    def set(self, key: str, value: tuple):
        try:
            self._connect()
            count, start_time, window = value
            self._redis.setex(key, window, json.dumps([count, start_time, window]))
        except Exception:
            pass

    def cleanup(self):
        # Redis keys auto-expire via setex, no manual cleanup needed
        pass


# 工厂函数
def _get_rate_store() -> RateLimitStore:
    backend = os.getenv("RATE_LIMIT_BACKEND", "memory")
    if backend == "redis":
        global _redis_store
        if _redis_store is None:
            try:
                _redis_store = RedisRateLimitStore()
            except Exception:
                from logger import logger
                logger.warning("Redis 不可用，降级到内存限流（多 worker 下限流不共享）")
                _redis_store = _memory_store
        return _redis_store
    return _memory_store


_memory_store = MemoryRateLimitStore()
_redis_store = None


def rate_limit(max_requests: int = 20, window: int = 60):
    """
    IP 维度速率限制装饰器：window 秒内最多 max_requests 次。
    未来可通过 RATE_LIMIT_BACKEND=redis 切换到分布式限流。
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = _get_client_ip()
            key = f"rl:{ip}:{f.__name__}"
            now = time.time()
            store = _get_rate_store()
            store.cleanup()

            entry = store.get(key)
            if entry:
                count, start, _ = entry
                if now - start < window:
                    if count >= max_requests:
                        return jsonify({
                            "error": "请求过于频繁，请稍后再试",
                            "retry_after": int(window - (now - start))
                        }), 429
                    store.set(key, (count + 1, start, window))
                else:
                    store.set(key, (1, now, window))
            else:
                store.set(key, (1, now, window))

            return f(*args, **kwargs)
        return wrapped
    return decorator


# ============================================================
# 输入校验
# ============================================================

def validate_input(schema: dict, data: dict) -> tuple:
    """
    简易 schema 校验，返回 (is_valid, cleaned_dict, errors)
    schema 示例:
    {"email": {"type": "email", "required": True, "maxlen": 100}}
    """
    cleaned = {}
    errors = []

    for field, rules in schema.items():
        val = data.get(field)

        if rules.get("required") and (val is None or (isinstance(val, str) and not val.strip())):
            errors.append(f"{field} 为必填项")
            continue

        if val is None:
            cleaned[field] = rules.get("default", None)
            continue

        if isinstance(val, str):
            val = val.strip()

        ftype = rules.get("type", "str")
        if ftype == "email":
            if not isinstance(val, str) or "@" not in val:
                errors.append(f"{field} 格式不正确，需为有效邮箱")
                continue
            val = val.lower()
        elif ftype == "phone":
            if not isinstance(val, str) or len(val) < 6:
                errors.append(f"{field} 格式不正确")
                continue
        elif ftype == "str":
            if not isinstance(val, str):
                val = ""
            if "maxlen" in rules and len(val) > rules["maxlen"]:
                val = val[:rules["maxlen"]]
        elif ftype == "int":
            try:
                val = int(val)
            except (TypeError, ValueError):
                errors.append(f"{field} 须为整数")
                continue

        cleaned[field] = val

    for field, rules in schema.items():
        if field not in cleaned and "default" in rules:
            cleaned[field] = rules["default"]

    return len(errors) == 0, cleaned, errors
