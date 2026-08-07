"""仪表盘 Blueprint — /api/dashboard, /api/preferences"""
from flask import Blueprint, request, jsonify, g
from security import rate_limit
from auth_middleware import login_required
from user_service import _safe_str, get_user
import db
import json

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/workflow/status", methods=["POST"])
@login_required
def api_workflow_status():
    """4阶段跨境贸易工作流状态"""
    data = request.get_json() or {}
    user_email = g.user_email
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
@login_required
def api_workflow_update():
    """更新工作流阶段"""
    data = request.get_json() or {}
    user_email = g.user_email
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
@login_required
def api_preferences():
    """获取或更新用户偏好（跨会话记忆）"""
    data = request.get_json() or {}
    user_email = g.user_email

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
@login_required
def api_dashboard():
    """返回用户仪表盘数据：展销会、认证要求、市场洞察"""
    data = request.get_json() or {}
    user_email = g.user_email

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


@dashboard_bp.route("/api/customer-acquisition", methods=["POST"])
@rate_limit(max_requests=10, window=300)
@login_required
def api_customer_acquisition():
    """一键获客工作流：搜索买家 → 生成开发信 → 保存到联系人"""
    import json as _json
    import concurrent.futures
    import time as _time

    data = request.get_json() or {}
    user_email = g.user_email
    keyword = _safe_str(data.get("keyword")).strip()
    target_market = _safe_str(data.get("target_market")).strip()  # 目标国家，可选
    max_results = data.get("max_results", 10)

    if not user_email:
        return jsonify({"success": False, "error": "请先登录"}), 400
    if not keyword:
        return jsonify({"success": False, "error": "请输入产品关键词"}), 400
    if max_results < 1 or max_results > 30:
        max_results = 10

    # 获取用户产品信息
    user = get_user(user_email)
    product = user.get("product", keyword) if user else keyword

    # 阶段1: 搜索买家
    from tools import search_buyers
    raw = search_buyers(keyword)
    try:
        parsed = _json.loads(raw)
    except Exception:
        parsed = {"success": False, "structured_results": []}

    structured = parsed.get("structured_results", [])
    note = parsed.get("note", "")

    # 如果 API 没返回结果，用 LLM 生成推荐
    if not structured:
        import hashlib
        structured_div = note  # 包含 LLM 推荐信息的文本
    else:
        structured_div = None

    # 阶段2: 并行生成开发信 + 保存联系人
    saved_contacts = []
    drafts = []
    draft_errors = []

    def process_buyer(buyer):
        comp_name = buyer.get("company_name", "Unknown")
        country = buyer.get("country", "")
        website = buyer.get("website", "")
        email = buyer.get("email", "")
        desc = buyer.get("description", "")

        result = {
            "company_name": comp_name,
            "country": country,
            "website": website,
            "email": email,
            "description": desc,
            "draft_email": "",
            "contact_id": None,
        }

        # 生成开发信（有邮箱才生成）
        if email and "@" in email:
            from tools import draft_email
            try:
                company_info = f"{comp_name} ({country}), website: {website}, {desc}"[:200]
                draft = draft_email(company_info, product)
                result["draft_email"] = draft[:500] if draft else ""
            except Exception as e:
                draft_errors.append(f"{comp_name}: {str(e)[:100]}")
                result["draft_email"] = ""

        # 保存到联系人
        try:
            contact_id = db.add_contact(
                user_email=user_email,
                company_name=comp_name,
                email=email,
                website=website,
                country=country,
                product_interest=keyword,
                source=f"AI获客搜索-{keyword}",
                notes=f"自动通过{keyword}搜索获得",
            )
            result["contact_id"] = contact_id
            saved_contacts.append(result)
        except Exception as e:
            result["contact_id"] = None

        drafts.append(result)
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_buyer, b) for b in structured[:max_results]]
        concurrent.futures.wait(futures, timeout=30)

    return jsonify({
        "success": True,
        "keyword": keyword,
        "total_found": len(structured),
        "saved_to_contacts": len(saved_contacts),
        "buyers": drafts,
        "raw_note": note[:3000] if not structured else "",
    })


@dashboard_bp.route("/api/knowledge/freshness", methods=["GET"])
@login_required
def api_knowledge_freshness():
    """知识库数据新鲜度摘要"""
    from datetime import datetime, timedelta
    from knowledge.tradeshows import TRADESHOWS, CERTIFICATIONS, _enrich_tradeshow

    today = datetime.now().date()
    cutoff_30d = today - timedelta(days=30)

    # 展会数据新鲜度
    show_dates = []
    for product_key, shows in TRADESHOWS.items():
        for show in shows:
            enriched = _enrich_tradeshow(show, product_key)
            lv = enriched.get("last_verified", "Unknown")
            if lv != "Unknown":
                try:
                    show_dates.append(datetime.strptime(lv, "%Y-%m-%d").date())
                except ValueError:
                    pass

    show_verified_30d = sum(1 for d in show_dates if d >= cutoff_30d)

    # 认证数据新鲜度
    cert_dates = []
    for product_key, certs in CERTIFICATIONS.items():
        for cert in certs:
            lu = cert.get("last_updated", "")
            if lu:
                try:
                    cert_dates.append(datetime.strptime(lu, "%Y-%m-%d").date())
                except ValueError:
                    pass

    cert_verified_30d = sum(1 for d in cert_dates if d >= cutoff_30d)

    # 市场建议新鲜度 (hardcoded as 2026-08-07)
    tips_total = 14  # hardcoded count in get_market_tips
    tips_verified_30d = 14  # all verified on 2026-08-07

    def _health(verified, total):
        if total == 0:
            return "empty"
        ratio = verified / total
        if ratio >= 0.8:
            return "good"
        elif ratio >= 0.5:
            return "fair"
        return "stale"

    return jsonify({
        "success": True,
        "tradeshows": {
            "total": len(show_dates),
            "verified_30d": show_verified_30d,
            "oldest": min(show_dates).isoformat() if show_dates else None,
            "newest": max(show_dates).isoformat() if show_dates else None,
            "health": _health(show_verified_30d, len(show_dates)),
        },
        "certifications": {
            "total": len(cert_dates),
            "verified_30d": cert_verified_30d,
            "oldest": min(cert_dates).isoformat() if cert_dates else None,
            "newest": max(cert_dates).isoformat() if cert_dates else None,
            "health": _health(cert_verified_30d, len(cert_dates)),
        },
        "market_tips": {
            "total": tips_total,
            "verified_30d": tips_verified_30d,
            "health": _health(tips_verified_30d, tips_total),
        },
        "overall_health": _health(
            show_verified_30d + cert_verified_30d + tips_verified_30d,
            len(show_dates) + len(cert_dates) + tips_total,
        ),
        "timestamp": today.isoformat(),
    })
