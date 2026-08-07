"""SMTP 配置管理 — 通过 API 读写，存储到 SQLite KV（密码加密存储）"""
import json
import os
from smtp_crypto import encrypt_password, decrypt_password


def load_config() -> dict:
    import db
    cfg = db.kv_get("smtp_config")
    if cfg is not None:
        # 迁移旧明文密码 → 加密
        if "smtp_password" in cfg and "smtp_password_encrypted" not in cfg:
            cfg["smtp_password_encrypted"] = encrypt_password(cfg.pop("smtp_password"))
            db.kv_set("smtp_config", cfg)
        # 解密返回
        if cfg.get("smtp_password_encrypted"):
            cfg["smtp_password"] = decrypt_password(cfg["smtp_password_encrypted"])
        return cfg
    # 首次从 JSON 文件迁移
    if os.path.exists("smtp_settings.json"):
        try:
            with open("smtp_settings.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # 迁移时即加密
            if cfg.get("smtp_password"):
                cfg["smtp_password_encrypted"] = encrypt_password(cfg.pop("smtp_password"))
            db.kv_set("smtp_config", cfg)
            return load_config()
        except (json.JSONDecodeError, IOError):
            pass
    return {"smtp_email": "", "smtp_password_encrypted": "", "smtp_password": "", "sender_name": ""}


def save_config(email: str, password: str, name: str = ""):
    import db
    db.kv_set("smtp_config", {
        "smtp_email": email,
        "smtp_password_encrypted": encrypt_password(password),
        "sender_name": name,
    })


def is_configured() -> bool:
    cfg = load_config()
    return bool(cfg.get("smtp_email") and cfg.get("smtp_password"))
