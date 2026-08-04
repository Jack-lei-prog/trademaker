"""
简易 TTL 缓存（线程安全）
"""
import time
import json
import hashlib
import threading
from functools import wraps

_cache = {}
_cache_lock = threading.Lock()
MAX_ENTRIES = 500


def _make_key(*args, **kwargs) -> str:
    raw = json.dumps(args, sort_keys=True, ensure_ascii=False)
    raw += json.dumps(kwargs, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def cached(ttl: int = 300):
    """
    装饰器：缓存函数返回值 ttl 秒（线程安全）
    用法: @cached(ttl=3600)   # 缓存 1 小时
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            key = f"{f.__name__}:{_make_key(*args, **kwargs)}"
            now = time.time()

            with _cache_lock:
                if key in _cache:
                    val, expires = _cache[key]
                    if now < expires:
                        return val
                    del _cache[key]

            result = f(*args, **kwargs)

            with _cache_lock:
                _cache[key] = (result, now + ttl)

                # 清理超出上限的条目
                if len(_cache) > MAX_ENTRIES:
                    expired = [k for k, v in _cache.items() if now > v[1]]
                    for k in expired:
                        _cache.pop(k, None)

            return result
        return wrapped
    return decorator


def invalidate(name: str = ""):
    """清除匹配名称的缓存"""
    with _cache_lock:
        to_delete = [k for k in _cache if name in k]
        for k in to_delete:
            del _cache[k]


def stats() -> dict:
    """缓存统计"""
    with _cache_lock:
        return {"entries": len(_cache)}
