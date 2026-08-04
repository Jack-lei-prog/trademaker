"""SMTP 配置管理 — 通过 API 读写，存储到 SQLite KV"""
import json
import os


def load_config() -> dict:
    import db
    cfg = db.kv_get("smtp_config")
    if cfg is not None:
        return cfg
    # 首次从 JSON 文件迁移
    if os.path.exists("smtp_settings.json"):
        try:
            with open("smtp_settings.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
            db.kv_set("smtp_config", cfg)
            return cfg
        except (json.JSONDecodeError, IOError):
            pass
    return {"smtp_email": "", "smtp_password": "", "sender_name": ""}


def save_config(email: str, password: str, name: str = ""):
    import db
    db.kv_set("smtp_config", {
        "smtp_email": email,
        "smtp_password": password,
        "sender_name": name,
    })


def is_configured() -> bool:
    cfg = load_config()
    return bool(cfg.get("smtp_email") and cfg.get("smtp_password"))
