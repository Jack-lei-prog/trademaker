"""仪表盘 Blueprint — /api/dashboard, /api/preferences"""
from flask import Blueprint, request, jsonify
from user_service import _safe_str, get_user
import db
import json

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/preferences", methods=["POST"])
def api_preferences():
    """获取或更新用户偏好（跨会话记忆）"""
    data = request.get_json() or {}
    user_email = _safe_str(data.get("user_email")).strip().lower()

    if not user_email:
        return jsonify({"success": False, "error": "请先登录"}), 400

    prefs = db.kv_get(f"prefs:{user_email}") or {
        "target_markets": [],
        "preferred_categories": [],
        "language": "zh",
        "last_searches": [],
    }

    # 如果是更新请求
    if data.get("update"):
        for key in ["target_markets", "preferred_categories", "language"]:
            if key in data:
                prefs[key] = data[key]
        # 记录搜索历史（最多保留10条）
        if data.get("search_query"):
            prefs["last_searches"] = ([data["search_query"]] + prefs.get("last_searches", []))[:10]
        db.kv_set(f"prefs:{user_email}", prefs)
        return jsonify({"success": True, "preferences": prefs})

    return jsonify({"success": True, "preferences": prefs})


@dashboard_bp.route("/api/dashboard", methods=["POST"])
def api_dashboard():
    """返回用户仪表盘数据：展销会、认证要求、市场洞察"""
    data = request.get_json() or {}
    user_email = _safe_str(data.get("user_email")).strip().lower()

    if not user_email:
        return jsonify({"success": False, "error": "请先登录"}), 400

    user = get_user(user_email)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404

    product = user.get("product", "")
    company = user.get("company", "")
    identity = user.get("identity", "seller")

    # 展销会匹配
    from knowledge.tradeshows import find_tradeshows, find_certifications, get_market_tips
    tradeshows = find_tradeshows(product)
    certifications = find_certifications(product)
    market_tips = get_market_tips(product)

    # 统计概览
    contacts = db.get_contacts(user_email)
    pending_contacts = [c for c in contacts if c.get("status") == "pending"]
    contacted_count = sum(1 for c in contacts if c.get("status") == "contacted")
    replied_count = sum(1 for c in contacts if c.get("status") == "replied")
    reminders = db.get_due_reminders(user_email)

    return jsonify({
        "success": True,
        "user": {
            "email": user_email,
            "company": company,
            "product": product,
            "identity": identity,
        },
        "tradeshows": tradeshows,
        "certifications": certifications,
        "market_tips": market_tips,
        "stats": {
            "total_contacts": len(contacts),
            "pending_contacts": len(pending_contacts),
            "contacted": contacted_count,
            "replied": replied_count,
            "due_reminders": len(reminders),
        }
    })
