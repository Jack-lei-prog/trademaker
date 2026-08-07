# -*- coding: utf-8 -*-
"""
SMTP 密码加密模块 — 使用 Fernet 对称加密
密钥来源（优先级）: SMTP_ENCRYPTION_KEY 环境变量 → DB 中自动生成 → 首次运行自动生成
"""
import base64
import os
from cryptography.fernet import Fernet
import db
from config import SMTP_ENCRYPTION_KEY as _ENV_KEY

_cipher = None


def _get_key() -> bytes:
    """获取或生成加密密钥（持久化到 DB kv_store）"""
    # 1. 环境变量提供
    if _ENV_KEY:
        key = _ENV_KEY
        if isinstance(key, str):
            key = key.encode()
        # 确保是 32 字节 urlsafe base64 格式
        try:
            # 尝试解码验证格式
            padded = key + b'=' * (-len(key) % 4)
            decoded = base64.urlsafe_b64decode(padded)
            if len(decoded) == 32:
                return base64.urlsafe_b64encode(decoded)
        except Exception:
            pass
        # 不是有效 Fernet key，用它的 SHA256 哈希派生
        import hashlib
        derived = hashlib.sha256(key).digest()
        return base64.urlsafe_b64encode(derived)

    # 2. DB 中已有
    stored = db.kv_get("smtp_encryption_key")
    if stored:
        return stored.encode()

    # 3. 首次运行 — 自动生成并存到 DB
    key = Fernet.generate_key()
    db.kv_set("smtp_encryption_key", key.decode())
    return key


def _get_cipher():
    """懒加载 Fernet 密码器"""
    global _cipher
    if _cipher is None:
        _cipher = Fernet(_get_key())
    return _cipher


def encrypt_password(plaintext: str) -> str:
    """加密密码，返回 base64 token 字符串"""
    if not plaintext:
        return ""
    return _get_cipher().encrypt(plaintext.encode()).decode()


def decrypt_password(token: str) -> str:
    """解密密码，返回明文"""
    if not token:
        return ""
    try:
        return _get_cipher().decrypt(token.encode()).decode()
    except Exception:
        # 解密失败：可能是旧版明文密码或旧密钥
        # 如果是旧明文格式（不像 base64），直接返回
        import re
        if re.match(r'^[A-Za-z0-9+/=]+$', token) and len(token) > 20:
            # 像加密 token 但解密失败 — 可能是换了密钥
            return ""
        # 不像加密 token — 可能是旧明文密码，直接返回
        return token
