"""客户联系管理 Blueprint — /api/contacts/*"""
from flask import Blueprint, request, jsonify
from security import rate_limit
from user_service import _safe_str
import db

contact_bp = Blueprint("contact", __name__)

CONTACT_METHODS = ["email", "linkedin", "phone", "whatsapp", "tradeshow", "website_form", "other"]
CONTACT_STATUSES = ["pending", "contacted", "replied", "negotiating", "ordered", "closed", "invalid"]


@contact_bp.route("/api/contacts/add", methods=["POST"])
@rate_limit(max_requests=30, window=60)
def api_add_contact():
    data = request.get_json() or {}
    user_email = _safe_str(data.get("user_email")).strip().lower()
    company_name = _safe_str(data.get("company_name")).strip()
    email = _safe_str(data.get("email")).strip()
    website = _safe_str(data.get("website")).strip()
    country = _safe_str(data.get("country")).strip()
    contact_person = _safe_str(data.get("contact_person")).strip()
    phone = _safe_str(data.get("phone")).strip()
    product_interest = _safe_str(data.get("product_interest")).strip()
    contact_method = _safe_str(data.get("contact_method", "email")).strip()
    source = _safe_str(data.get("source")).strip()
    notes = _safe_str(data.get("notes")).strip()
    remind_days = int(data.get("remind_days", 7)) if data.get("remind_days") else 7

    if not user_email:
        return jsonify({"success": False, "error": "请先登录"}), 400
    if not company_name:
        return jsonify({"success": False, "error": "公司名称不能为空"}), 400
    if contact_method not in CONTACT_METHODS:
        contact_method = "email"

    cid = db.add_contact(
        user_email=user_email, company_name=company_name, email=email,
        website=website, country=country, contact_person=contact_person,
        phone=phone, product_interest=product_interest,
        contact_method=contact_method, source=source, notes=notes,
        next_remind_days=remind_days)
    return jsonify({"success": True, "contact_id": cid})


@contact_bp.route("/api/contacts/list", methods=["POST"])
def api_list_contacts():
    data = request.get_json() or {}
    user_email = _safe_str(data.get("user_email")).strip().lower()
    status = _safe_str(data.get("status")).strip()
    if not user_email:
        return jsonify({"success": False, "error": "请先登录"}), 400
    contacts = db.get_contacts(user_email, status=status)
    reminders = db.get_due_reminders(user_email)
    return jsonify({
        "success": True,
        "contacts": contacts,
        "total": len(contacts),
        "due_reminders": len(reminders),
        "reminder_ids": [r["id"] for r in reminders],
    })


@contact_bp.route("/api/contacts/update", methods=["POST"])
def api_update_contact():
    data = request.get_json() or {}
    user_email = _safe_str(data.get("user_email")).strip().lower()
    contact_id = data.get("contact_id")
    if not user_email or not contact_id:
        return jsonify({"success": False, "error": "缺少参数"}), 400

    kwargs = {}
    for field in ["status", "notes", "contact_method", "email", "phone",
                  "contact_person", "product_interest"]:
        if field in data and data[field] is not None:
            val = _safe_str(data[field]).strip()
            if val:
                kwargs[field] = val
    # 重新设置提醒
    if data.get("remind_days"):
        from datetime import datetime, timedelta
        kwargs["next_remind_at"] = (datetime.now() + timedelta(days=int(data["remind_days"]))).strftime("%Y-%m-%d %H:%M:%S")

    ok = db.update_contact(contact_id, user_email=user_email, **kwargs)
    return jsonify({"success": ok})


@contact_bp.route("/api/contacts/delete", methods=["POST"])
def api_delete_contact():
    data = request.get_json() or {}
    user_email = _safe_str(data.get("user_email")).strip().lower()
    contact_id = data.get("contact_id")
    if not user_email or not contact_id:
        return jsonify({"success": False, "error": "缺少参数"}), 400
    db.delete_contact(contact_id, user_email=user_email)
    return jsonify({"success": True})


@contact_bp.route("/api/contacts/stats", methods=["POST"])
def api_contact_stats():
    data = request.get_json() or {}
    user_email = _safe_str(data.get("user_email")).strip().lower()
    if not user_email:
        return jsonify({"success": False, "error": "请先登录"}), 400
    all_contacts = db.get_contacts(user_email)
    reminders = db.get_due_reminders(user_email)
    stats = {"total": len(all_contacts)}
    for s in CONTACT_STATUSES:
        stats[s] = sum(1 for c in all_contacts if c.get("status") == s)
    stats["due_reminders"] = len(reminders)
    return jsonify({"success": True, "stats": stats})
