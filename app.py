# -*- coding: utf-8 -*-
"""
外贸通 Web 应用 — 主入口
基于 Flask Blueprint 的模块化架构
"""
import time as _time
import uuid
import atexit
from flask import Flask, request, jsonify, g
from dotenv import load_dotenv
from logger import get_logger, log_request

load_dotenv()

app = Flask(__name__)
log = get_logger()

# 注册应用关闭钩子
atexit.register(lambda: __import__('db').close_all_connections())

# 初始化演示账号
try:
    from knowledge.demo import init_demo_user
    init_demo_user()
except Exception:
    pass

# ============================================================
# CORS 白名单
# ============================================================
ALLOWED_ORIGINS = {
    "http://127.0.0.1:5000",
    "http://localhost:5000",
    "http://192.168.1.100:5000",
}


# ============================================================
# 请求日志中间件
# ============================================================
@app.before_request
def _before_request():
    request._start_time = _time.time()
    # 为每个请求生成唯一 ID
    g.request_id = uuid.uuid4().hex[:12]


@app.after_request
def _after_request(response):
    # CORS 头
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS or not origin:
        response.headers["Access-Control-Allow-Origin"] = origin or "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

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
    import os as _os
    is_debug = _os.getenv("FLASK_DEBUG", "0") == "1"
    print("=" * 60)
    print("[TradeMaster] Foreign Trade Assistant Web Service Starting...")
    print("=" * 60)
    print(f"URL: http://127.0.0.1:5000  |  Debug: {is_debug}")
    print("=" * 60)
    app.run(debug=is_debug, host="0.0.0.0", port=5000)
