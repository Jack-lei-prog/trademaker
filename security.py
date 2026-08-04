"""
安全模块 — 速率限制 + 输入校验
"""
import time
import json
import re
import hashlib
from functools import wraps
from flask import request, jsonify

# 速率限制（内存版，最多存储 10000 个条目）
_rate_store = {}
MAX_RATE_ENTRIES = 10000


def _clean_rate_store():
    """定期清理过期条目"""
    if len(_rate_store) > MAX_RATE_ENTRIES:
        now = time.time()
        expired = [k for k, v in _rate_store.items() if v[0] + v[1] < now]
        for k in expired:
            del _rate_store[k]


def rate_limit(max_requests: int = 20, window: int = 60):
    """IP 维度速率限制装饰器：window 秒内最多 max_requests 次"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
            key = f"rl:{ip}:{f.__name__}"
            now = time.time()
            _clean_rate_store()

            if key in _rate_store:
                count, start, _ = _rate_store[key]
                if now - start < window:
                    if count >= max_requests:
                        return jsonify({"error": "请求过于频繁，请稍后再试", "retry_after": int(window - (now - start))}), 429
                    _rate_store[key] = (count + 1, start, window)
                else:
                    _rate_store[key] = (1, now, window)
            else:
                _rate_store[key] = (1, now, window)

            return f(*args, **kwargs)
        return wrapped
    return decorator


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

        # required check
        if rules.get("required") and (val is None or (isinstance(val, str) and not val.strip())):
            errors.append(f"{field} 为必填项")
            continue

        if val is None:
            cleaned[field] = rules.get("default", None)
            continue

        # type check
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
                val = val[: rules["maxlen"]]
        elif ftype == "int":
            try:
                val = int(val)
            except (TypeError, ValueError):
                errors.append(f"{field} 须为整数")
                continue

        cleaned[field] = val

    # defaults for missing optional fields
    for field, rules in schema.items():
        if field not in cleaned and "default" in rules:
            cleaned[field] = rules["default"]

    return len(errors) == 0, cleaned, errors
