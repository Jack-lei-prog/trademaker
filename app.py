# -*- coding: utf-8 -*-
"""
外贸通 Web 应用 — 主入口
基于 Flask Blueprint 的模块化架构
"""
import os as _os

import time as _time
import uuid
import atexit
from flask import Flask, request, jsonify, g
from dotenv import load_dotenv
from logger import get_logger, log_request

# 从项目目录强制加载 .env（覆盖系统环境变量）
_ENV_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".env")
if _os.path.exists(_ENV_PATH):
    load_dotenv(_ENV_PATH, override=True)
else:
    load_dotenv()

app = Flask(__name__)

# 安全密钥（config.py 已校验，缺失则启动失败）
from config import SECRET_KEY
app.secret_key = SECRET_KEY
log = get_logger()

# 注册应用关闭钩子
atexit.register(lambda: __import__('db').close_all_connections())

# 初始化演示账号
try:
    from knowledge.demo import init_demo_user
    init_demo_user()
except Exception as _e:
    import logging
    logging.getLogger("TradeMaster").warning(f"Demo init skipped: {_e}")

# ============================================================
# CORS — 始终使用显式白名单（从 CORS_ORIGINS 环境变量读取）
# ============================================================
from config import CORS_ORIGINS
ALLOWED_ORIGINS = CORS_ORIGINS


# ============================================================
# 请求日志中间件
# ============================================================
@app.before_request
def _before_request():
    request._start_time = _time.time()
    # 为每个请求生成唯一 ID
    g.request_id = uuid.uuid4().hex[:12]


@app.before_request
def _handle_preflight():
    """处理 OPTIONS 预检请求"""
    if request.method == "OPTIONS":
        resp = app.make_default_options_response()
        origin = request.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Access-Control-Max-Age"] = "3600"
        return resp


@app.after_request
def _after_request(response):
    # CORS 头（始终使用显式白名单）
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
    elif not origin:
        response.headers["Access-Control-Allow-Origin"] = "*"
    # 非白名单来源：不设 CORS 头，浏览器将拒绝
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

    # 安全响应头
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # CSP（前端为单文件 index.html，允许内联脚本和 CDN）
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https:; "
        "font-src 'self' https://cdn.jsdelivr.net"
    )

    # HSTS（生产环境建议开启）
    if not __import__('os').getenv("FLASK_DEBUG", "0") == "1":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # 请求 ID
    req_id = getattr(g, "request_id", "")
    if req_id:
        response.headers["X-Request-ID"] = req_id

    # 日志
    elapsed = (_time.time() - getattr(request, "_start_time", _time.time())) * 1000
    log_request(
        ip=request.headers.get("X-Forwarded-For", request.remote_addr or "?"),
        method=request.method,
        path=request.path,
        status=response.status_code,
        duration_ms=elapsed,
    )
    return response


# ============================================================
# 注册 Blueprints
# ============================================================
from blueprints.auth_bp import auth_bp
from blueprints.chat_bp import chat_bp
from blueprints.email_bp import email_bp
from blueprints.inquiry_bp import inquiry_bp
from blueprints.evaluate_bp import evaluate_bp
from blueprints.contact_bp import contact_bp
from blueprints.dashboard_bp import dashboard_bp
from blueprints.doll_bp import doll_bp

app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(email_bp)
app.register_blueprint(inquiry_bp)
app.register_blueprint(evaluate_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(doll_bp)


# ============================================================
# 全局错误处理
# ============================================================
@app.errorhandler(400)
def _bad_request(_e):
    return jsonify({"error": True, "message": "请求格式错误"}), 400


@app.errorhandler(404)
def _not_found(_e):
    return jsonify({"error": True, "message": "接口不存在"}), 404


@app.errorhandler(405)
def _method_not_allowed(_e):
    return jsonify({"error": True, "message": "不支持的请求方法"}), 405


@app.errorhandler(500)
def _server_error(e):
    log.error(f"Internal Server Error: {str(e)}")
    return jsonify({"error": True, "message": "服务器内部错误，请稍后重试"}), 500


@app.errorhandler(Exception)
def _unhandled(e):
    log.error(f"Unhandled exception: {type(e).__name__}: {str(e)}")
    return jsonify({"error": True, "message": "服务器内部错误"}), 500


# ============================================================
# 启动
# ============================================================
if __name__ == "__main__":
    is_debug = _os.getenv("FLASK_DEBUG", "0") == "1"
    print("=" * 60)
    print("[TradeMaster] Foreign Trade Assistant Web Service Starting...")
    print("=" * 60)
    print(f"URL: http://127.0.0.1:5000  |  Debug: {is_debug}")
    print("=" * 60)
    app.run(debug=is_debug, host="0.0.0.0", port=5000)
