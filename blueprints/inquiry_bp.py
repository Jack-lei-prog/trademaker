"""询盘 Blueprint — /api/inquiry/*"""
from flask import Blueprint, request, jsonify
from user_service import _safe_str, get_user
from inquiry_engine import process_inquiry_full, get_pending_inquiries, get_alerts

inquiry_bp = Blueprint("inquiry", __name__)


@inquiry_bp.route("/api/inquiry/process", methods=["POST"])
def process():
    data = request.get_json() or {}
    inquiry_text = _safe_str(data.get("inquiry_text")).strip()
    user_email = _safe_str(data.get("user_email")).strip().lower()
    if not inquiry_text:
        return jsonify({"success": False, "error": "Missing inquiry_text"}), 400

    user_product = user_company = user_phone = ""
    if user_email:
        user = get_user(user_email)
        if user:
            user_product, user_company, user_phone = user.get("product", ""), user.get("company", ""), user.get("phone", "")

    result = process_inquiry_full(inquiry_text, user_email, user_product, user_company, user_phone)
    return jsonify({"success": True, "result": result})


@inquiry_bp.route("/api/inquiry/pending", methods=["POST"])
def pending():
    data = request.get_json() or {}
    user_email = _safe_str(data.get("user_email")).strip().lower()
    pending_list = get_pending_inquiries(user_email)
    return jsonify({"success": True, "pending": pending_list, "count": len(pending_list)})


@inquiry_bp.route("/api/inquiry/alerts", methods=["POST"])
def alerts():
    data = request.get_json() or {}
    user_email = _safe_str(data.get("user_email")).strip().lower()
    alerts_list = get_alerts(user_email)
    return jsonify({"success": True, "alerts": alerts_list, "count": len(alerts_list)})
