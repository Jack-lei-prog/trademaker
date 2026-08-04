"""认证 Blueprint — /api/register, /api/login"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from security import rate_limit, validate_input
from user_service import _safe_str, _load_users, _save_users, get_user, _hash_password, authenticate_user

auth_bp = Blueprint("auth", __name__)


def _sanitize_user(user: dict) -> dict:
    """去除敏感字段后返回用户信息"""
    return {k: v for k, v in user.items() if k != "password_hash"}


@auth_bp.route("/api/register", methods=["POST"])
@rate_limit(max_requests=10, window=60)
def register():
    data = request.get_json() or {}
    ok, cleaned, errors = validate_input({
        "email": {"type": "email", "required": True, "maxlen": 100},
        "password": {"type": "str", "required": True, "maxlen": 100},
        "phone": {"type": "phone", "required": True, "maxlen": 30},
        "company": {"type": "str", "maxlen": 200, "default": ""},
        "product": {"type": "str", "required": True, "maxlen": 200},
        "identity": {"type": "str", "maxlen": 20, "default": "seller"},
    }, data)
    if not ok:
        return jsonify({"success": False, "error": "; ".join(errors)}), 400

    email = cleaned["email"].strip().lower()
    password = cleaned["password"].strip()
    phone = cleaned["phone"].strip()
    company = cleaned["company"].strip()
    product = cleaned["product"].strip()
    identity = cleaned["identity"] or "seller"

    if "@" not in email:
        return jsonify({"success": False, "error": "请输入有效的邮箱地址"}), 400
    if len(password) < 6:
        return jsonify({"success": False, "error": "密码长度不能少于6位"}), 400
    if identity not in ("seller", "boss"):
        identity = "seller"

    users = _load_users()
    if email in users:
        return jsonify({"success": False, "error": "该邮箱已注册，请直接登录"}), 400

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    user = {
        "email": email, "phone": phone, "company": company,
        "product": product, "identity": identity,
        "password_hash": _hash_password(password),
        "registered_at": now, "last_login": now
    }
    users[email] = user
    _save_users(users)
    return jsonify({"success": True, "user": _sanitize_user(user)})


@auth_bp.route("/api/login", methods=["POST"])
@rate_limit(max_requests=20, window=60)
def login():
    data = request.get_json() or {}
    email = _safe_str(data.get("email")).strip().lower()
    password = _safe_str(data.get("password", ""))

    if not email or not password:
        return jsonify({"success": False, "error": "请输入邮箱和密码"}), 400

    # Demo账号自动修复：如果不存在则自动创建
    if email == "demo@trademaster.com" and password == "demo2024":
        users = _load_users()
        if email not in users:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            users[email] = {
                "email": email, "phone": "13800138001",
                "company": "深圳声海科技有限公司", "product": "bluetooth earphone",
                "identity": "seller",
                "password_hash": _hash_password(password),
                "registered_at": now, "last_login": now
            }
            _save_users(users)

    user = authenticate_user(email, password)
    if not user:
        return jsonify({"success": False, "error": "邮箱或密码错误"}), 401

    # 更新登录时间
    user["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    users = _load_users()
    users[email] = user
    _save_users(users)

    return jsonify({"success": True, "user": _sanitize_user(user)})
