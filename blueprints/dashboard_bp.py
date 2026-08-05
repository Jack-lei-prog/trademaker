"""仪表盘 Blueprint — /api/dashboard, /api/preferences"""
from flask import Blueprint, request, jsonify
from user_service import _safe_str, get_user
import db
import json

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/workflow/status", methods=["POST"])
def api_workflow_status():
    """4阶段跨境贸易工作流状态"""
    data = request.get_json() or {}
    user_email = _safe_str(data.get("user_email")).strip().lower()
    if not user_email:
        return jsonify({"success": False, "error": "请先登录"}), 400

    # 从会话metadata读取工作流进度
    meta = db.get_session_metadata(user_email, user_email)
    workflow = meta.get("workflow", {
        "stage": 1,
        "stages": [
            {"id":1,"name":"市场调研","icon":"🔍","status":"active","desc":"搜索买家+分析市场"},
            {"id":2,"name":"合规审查","icon":"📋","status":"pending","desc":"认证要求+法规检查"},
            {"id":3,"name":"商务沟通","icon":"✉️","status":"pending","desc":"开发信+报价+询盘"},
            {"id":4,"name":"成交交付","icon":"✅","status":"pending","desc":"PI/合同+物流+跟进"},
        ],
        "completed_actions": [],
        "next_action": "搜索目标市场买家"
    })
    return jsonify({"success": True, "workflow": workflow})


@dashboard_bp.route("/api/workflow/update", methods=["POST"])
def api_workflow_update():
    """更新工作流阶段"""
    data = request.get_json() or {}
    user_email = _safe_str(data.get("user_email")).strip().lower()
    stage = data.get("stage", 1)
    if not user_email:
        return jsonify({"success": False, "error": "请先登录"}), 400

    meta = db.get_session_metadata(user_email, user_email)
    wf = meta.get("workflow", {})
    stages = wf.get("stages", [])
    for s in stages:
        if s["id"] < stage: s["status"] = "done"
        elif s["id"] == stage: s["status"] = "active"
        else: s["status"] = "pending"
    wf["stage"] = stage
    meta["workflow"] = wf
    db.update_session_metadata(user_email, user_email, meta)
    return jsonify({"success": True, "workflow": wf})


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

    # 邮件待跟进统计
    from services import get_pending_followups
    pending_emails = get_pending_followups(user_email) if user_email else []

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
            "pending_emails": len(pending_emails),
            "pending_email_list": [{"to": e.get("to",""), "subject": e.get("subject",""), "days_ago": e.get("days_ago",0)} for e in pending_emails[:5]],
        }
    })
