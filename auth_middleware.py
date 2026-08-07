# -*- coding: utf-8 -*-
"""
JWT 认证中间件 — 创建/验证令牌 + @login_required 装饰器
"""
import functools
from datetime import datetime, timedelta, timezone
import jwt
from flask import request, jsonify, g
from config import SECRET_KEY, JWT_EXPIRY_HOURS


def create_token(user_email: str) -> str:
    """为用户签发 JWT 令牌"""
    payload = {
        "sub": user_email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    """解码并验证 JWT。成功返回 payload，失败返回 None"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def login_required(f):
    """
    JWT 鉴权装饰器。
    从 Authorization: Bearer <token> 取 JWT，验证通过后设置 g.user_email。
    鉴权失败返回 401。
    """
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = decode_token(token)
            if payload:
                g.user_email = payload.get("sub", "")
                return f(*args, **kwargs)

        return jsonify({"success": False, "error": "请先登录"}), 401

    return wrapped


def optional_login(f):
    """
    可选鉴权装饰器。
    有 JWT 时设置 g.user_email，没有时 g.user_email 为空字符串。
    用于 chat 等可以匿名使用的端点。
    """
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        g.user_email = ""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            payload = decode_token(auth_header[7:])
            if payload:
                g.user_email = payload.get("sub", "")
        return f(*args, **kwargs)

    return wrapped
