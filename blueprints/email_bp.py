"""邮件 Blueprint — send_email, emails/*, email/*"""
import json
from flask import Blueprint, request, jsonify, Response
from security import rate_limit
from email_tracker import record_open, TRACKING_GIF, classify_intent, classify_and_update
from user_service import _safe_str
from services import (
    execute_tool, track_sent_email,
    get_user_emails, get_pending_followups, update_email_status, get_email_stats
)
import mailer

email_bp = Blueprint("email", __name__)


@email_bp.route("/api/send_email", methods=["POST"])
def api_send_email():
    data = request.get_json()
    to_email = _safe_str(data.get("to_email")).strip()
    subject = _safe_str(data.get("subject")).strip()
    body = _safe_str(data.get("body")).strip()
    to_name = _safe_str(data.get("to_name")).strip()
    user_email = _safe_str(data.get("user_email")).strip()

    if not to_email or not subject or not body:
        return jsonify({"success": False, "error": "缺少必要参数：to_email, subject, body"}), 400

    result = execute_tool("send_email", {"to_email": to_email, "subject": subject, "body": body, "to_name": to_name})
    try:
        parsed = json.loads(result) if isinstance(result, str) else result
    except (json.JSONDecodeError, TypeError):
        return jsonify({"success": False, "error": str(result)}), 500

    if parsed.get("success"):
        eid, tid = track_sent_email(user_email or "", to_email, to_name, subject, body)
        host = request.host_url.rstrip("/")
        parsed["tracking_id"] = tid
        parsed["tracking_pixel"] = f'<img src="{host}/api/email/open/{tid}" width="1" height="1" alt="">'
        # 自动加入跟进队列
        try:
            from inquiry_engine import add_to_followup_queue
            add_to_followup_queue(
                user_email=user_email or "", client_email=to_email,
                client_name=to_name, subject=subject,
                inquiry_text=body[:200], intent_type="",
                auto_followup_days=3)
        except Exception:
            pass

    return jsonify(parsed)


@email_bp.route("/api/email/smtp_send", methods=["POST"])
def api_smtp_send():
    data = request.get_json()
    to_email = _safe_str(data.get("to_email")).strip()
    subject = _safe_str(data.get("subject")).strip()
    body = _safe_str(data.get("body")).strip()
    to_name = _safe_str(data.get("to_name")).strip()
    user_email = _safe_str(data.get("user_email")).strip()

    if not to_email or not subject or not body:
        return jsonify({"success": False, "error": "缺少必要参数"}), 400
    if not mailer.is_configured():
        return jsonify({"success": False, "error": "SMTP 未配置。请在 .env 中设置 SMTP_EMAIL 和 SMTP_PASSWORD", "hint": "打开 .env 文件配置QQ邮箱"}), 400

    result = mailer.send_email_smtp(to_email=to_email, subject=subject, body=body, to_name=to_name, from_name="")
    if result.get("success"):
        eid, tid = track_sent_email(user_email or "", to_email, to_name, subject, body)
        result["tracking_id"] = tid
    return jsonify(result)


@email_bp.route("/api/emails/sent", methods=["POST"])
def api_get_sent():
    data = request.get_json() or {}
    email = _safe_str(data.get("user_email")).strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Missing user_email"}), 400
    return jsonify({"success": True, "emails": get_user_emails(email)})


@email_bp.route("/api/emails/pending", methods=["POST"])
def api_pending():
    data = request.get_json() or {}
    email = _safe_str(data.get("user_email")).strip().lower()
    pending = get_pending_followups(email)
    return jsonify({"success": True, "pending": pending, "count": len(pending)})


@email_bp.route("/api/emails/status", methods=["POST"])
def api_status():
    data = request.get_json() or {}
    ue = _safe_str(data.get("user_email")).lower()
    te = _safe_str(data.get("to_email")).lower()
    st = _safe_str(data.get("status")).lower()
    if not ue or not te or st not in ("sent", "replied", "bounced", "no_reply"):
        return jsonify({"success": False, "error": "Invalid"}), 400
    r = update_email_status(ue, te, st)
    return jsonify({"success": True, "email": r} if r else {"success": False, "error": "Not found"})


@email_bp.route("/api/email/stats", methods=["POST"])
def api_stats():
    data = request.get_json() or {}
    email = _safe_str(data.get("user_email")).strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Missing user_email"}), 400
    return jsonify({"success": True, "stats": get_email_stats(email)})


@email_bp.route("/api/email/open/<tracking_id>", methods=["GET"])
def api_open(tracking_id):
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
    ua = request.headers.get("User-Agent", "")
    record_open(tracking_id, ip, ua)
    return Response(TRACKING_GIF, mimetype="image/gif",
                    headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@email_bp.route("/api/email/classify", methods=["POST"])
def api_classify():
    data = request.get_json() or {}
    user_email = _safe_str(data.get("user_email")).lower()
    to_email = _safe_str(data.get("to_email")).lower()
    reply_text = _safe_str(data.get("reply_text")).strip()
    subject = _safe_str(data.get("subject")).strip()
    if not reply_text:
        return jsonify({"success": False, "error": "Missing reply_text"}), 400
    result = classify_and_update(user_email, to_email, reply_text, subject) if user_email and to_email else classify_intent(reply_text, subject)
    return jsonify({"success": True, "intent": result})


@email_bp.route("/api/email/sync", methods=["POST"])
def api_sync():
    from services import _email_provider
    data = request.get_json() or {}
    email = _safe_str(data.get("user_email")).strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Missing user_email"}), 400
    new_replies = _email_provider.sync_inbox(email)
    return jsonify({"success": True, "new_replies": len(new_replies), "replies": new_replies})


# ============================================================
# SMTP 设置 — 页面配置
# ============================================================
@email_bp.route("/api/email/smtp_settings", methods=["GET"])
def api_smtp_get():
    from smtp_config import load_config
    cfg = load_config()
    return jsonify({"success": True, "config": {
        "smtp_email": cfg.get("smtp_email", ""),
        "sender_name": cfg.get("sender_name", ""),
        "has_password": bool(cfg.get("smtp_password", "")),
    }})


@email_bp.route("/api/email/smtp_settings", methods=["POST"])
def api_smtp_save():
    data = request.get_json() or {}
    email = _safe_str(data.get("smtp_email")).strip()
    pwd = _safe_str(data.get("smtp_password")).strip()
    name = _safe_str(data.get("sender_name")).strip()

    if not email or "@" not in email:
        return jsonify({"success": False, "error": "请输入有效的邮箱地址"}), 400
    if not pwd:
        return jsonify({"success": False, "error": "请输入邮箱授权码"}), 400

    from smtp_config import save_config
    save_config(email, pwd, name)
    return jsonify({"success": True, "message": "SMTP 配置已保存"})


@email_bp.route("/api/email/smtp_test", methods=["POST"])
def api_smtp_test():
    data = request.get_json() or {}
    email = _safe_str(data.get("smtp_email")).strip()
    pwd = _safe_str(data.get("smtp_password")).strip()
    name = _safe_str(data.get("sender_name")).strip()

    if not email or not pwd:
        return jsonify({"success": False, "error": "请填写邮箱和授权码"}), 400

    # 临时保存
    from smtp_config import save_config
    save_config(email, pwd, name)

    # 发送测试邮件给自己
    result = mailer.send_email_smtp(
        to_email=email, subject="TradeMaster SMTP 测试", body="这是一封测试邮件。\n\n如果你收到这封邮件，说明 SMTP 配置成功！\n\n— TradeMaster 外贸通",
        to_name="", from_name=name)
    return jsonify(result)
