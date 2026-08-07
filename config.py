# -*- coding: utf-8 -*-
"""
集中配置模块 — 所有环境变量读取和启动校验统一入口
其他模块统一 from config import xxx，不再散落 os.getenv 调用
"""
import os
import sys
from dotenv import load_dotenv

# 从项目目录强制加载 .env（覆盖系统环境变量）
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_ENV_PATH):
    load_dotenv(_ENV_PATH, override=True)
else:
    load_dotenv()

# ============================================================
# 安全关键配置 — 启动时校验
# ============================================================

SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY")
if not SECRET_KEY:
    print("[TradeMaster] FATAL: SECRET_KEY 环境变量未设置！")
    print("  请执行: python -c \"import secrets; print(secrets.token_hex(32))\" 生成密钥")
    print("  然后在 .env 中添加: SECRET_KEY=<生成的密钥>")
    sys.exit(1)

JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "168"))  # 默认7天

# SMTP 加密密钥（可选 — 不设置则自动生成并存到 DB）
SMTP_ENCRYPTION_KEY = os.getenv("SMTP_ENCRYPTION_KEY") or None

# ============================================================
# CORS — 所有环境都使用显式白名单
# ============================================================
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "http://127.0.0.1:5000,http://localhost:5000,http://192.168.1.100:5000")
CORS_ORIGINS = set(o.strip() for o in CORS_ORIGINS_STR.split(",") if o.strip())

# 可信代理地址（用于正确解析 X-Forwarded-For）
TRUSTED_PROXIES_STR = os.getenv("TRUSTED_PROXIES", "127.0.0.1,::1")
TRUSTED_PROXIES = set(o.strip() for o in TRUSTED_PROXIES_STR.split(",") if o.strip())

# ============================================================
# Flask
# ============================================================
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

# ============================================================
# LLM API（原有配置，保持兼容）
# ============================================================
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("SYNSCALE_API_KEY")
LLM_API_URL = os.getenv("LLM_API_URL") or "https://api.moonshot.cn/v1/chat/completions"
LLM_MODEL = os.getenv("LLM_MODEL") or os.getenv("SYNSCALE_MODEL_NAME") or "kimi-k2.7-code"

# 备用 API（services.py 自动读取，此处保留以保持兼容）
SYNSCALE_API_KEY = LLM_API_KEY
