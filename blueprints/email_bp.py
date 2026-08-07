"""邮件 Blueprint — send_email, emails/*, email/*（含两阶段确认发送）"""
import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, Response, g
from security import rate_limit
from auth_middleware import login_required
from email_tracker import record_open, TRACKING_GIF, classify_intent, classify_and_update
from user_service import _safe_str
from services import (
    execute_tool, track_sent_email,
    get_user_emails, get_pending_followups, update_email_status, get_email_stats
)
import mailer
import db

email_bp = Blueprint("email", __name__)


@email_bp.route("/api/send_email", methods=["POST"])
@login_required
def api_send_email():
    data = request.get_json()
    to_email = _safe_str(data.get("to_email")).strip()
    subject = _safe_str(data.get("subject")).strip()
    body = _safe_str(data.get("body")).strip()
    to_name = _safe_str(data.get("to_name")).strip()
    user_email = g.user_email

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
@rate_limit(max_requests=10, window=300)
@login_required
def api_smtp_send():
    data = request.get_json()
    to_email = _safe_str(data.get("to_email")).strip()
    subject = _safe_str(data.get("subject")).strip()
    body = _safe_str(data.get("body")).strip()
    to_name = _safe_str(data.get("to_name")).strip()
    user_email = g.user_email

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
@rate_limit(max_requests=30, window=60)
@login_required
def api_get_sent():
    data = request.get_json() or {}
    email = g.user_email
    emails = get_user_emails(email)
    # 如果没找到，也尝试加载所有邮件（兼容QQ邮箱发送场景）
    if not emails:
        from services import _email_provider
        all_data = _email_provider._load()
        emails = list(all_data.values())
    return jsonify({"success": True, "emails": emails})


@email_bp.route("/api/emails/pending", methods=["POST"])
@rate_limit(max_requests=30, window=60)
@login_required
def api_pending():
    data = request.get_json() or {}
    email = g.user_email
    pending = get_pending_followups(email)
    return jsonify({"success": True, "pending": pending, "count": len(pending)})


@email_bp.route("/api/emails/status", methods=["POST"])
@rate_limit(max_requests=30, window=60)
@login_required
def api_status():
    data = request.get_json() or {}
    ue = g.user_email
    te = _safe_str(data.get("to_email")).lower()
    st = _safe_str(data.get("status")).lower()
    reply_text = _safe_str(data.get("reply_text")).strip()

    if not ue or not te or st not in ("sent", "replied", "bounced", "no_reply"):
        return jsonify({"success": False, "error": "Invalid"}), 400
    r = update_email_status(ue, te, st)

    if r and st == "replied" and reply_text:
        from email_tracker import classify_intent
        intent = classify_intent(reply_text, r.get("subject",""))
        r["intent"] = intent.get("intent","")
        r["intent_brief"] = intent.get("brief","")

    return jsonify({"success": True, "email": r} if r else {"success": False, "error": "Not found"})


@email_bp.route("/api/email/stats", methods=["POST"])
@rate_limit(max_requests=30, window=60)
@login_required
def api_stats():
    data = request.get_json() or {}
    email = g.user_email
    return jsonify({"success": True, "stats": get_email_stats(email)})


@email_bp.route("/api/email/open/<tracking_id>", methods=["GET"])
def api_open(tracking_id):
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
    ua = request.headers.get("User-Agent", "")
    record_open(tracking_id, ip, ua)
    return Response(TRACKING_GIF, mimetype="image/gif",
                    headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@email_bp.route("/api/email/classify", methods=["POST"])
@rate_limit(max_requests=20, window=60)
@login_required
def api_classify():
    data = request.get_json() or {}
    user_email = g.user_email
    to_email = _safe_str(data.get("to_email")).lower()
    reply_text = _safe_str(data.get("reply_text")).strip()
    subject = _safe_str(data.get("subject")).strip()
    if not reply_text:
        return jsonify({"success": False, "error": "Missing reply_text"}), 400
    result = classify_and_update(user_email, to_email, reply_text, subject) if user_email and to_email else classify_intent(reply_text, subject)
    return jsonify({"success": True, "intent": result})


@email_bp.route("/api/email/sync", methods=["POST"])
@rate_limit(max_requests=5, window=300)
@login_required
def api_sync():
    """IMAP 收件箱同步 — 自动检测客户回复"""
    data = request.get_json() or {}
    email_addr = g.user_email

    try:
        from imap_sync import check_replies, is_imap_configured
        if not is_imap_configured():
            return jsonify({
                "success": False,
                "error": "IMAP 未配置。请在 SMTP 设置中填写邮箱和授权码（QQ邮箱需开启IMAP服务）",
                "hint": "QQ邮箱 → 设置 → 账户 → POP3/IMAP/SMTP服务 → 开启IMAP"
            }), 400

        replies = check_replies(email_addr)
        return jsonify({
            "success": True,
            "new_replies": len(replies),
            "replies": replies,
            "message": f"发现 {len(replies)} 条新回复" if replies else "未发现新的客户回复"
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"同步失败: {str(e)[:100]}"}), 500


# ============================================================
# SMTP 设置 — 页面配置
# ============================================================
@email_bp.route("/api/email/smtp_settings", methods=["GET"])
@login_required
def api_smtp_get():
    from smtp_config import load_config
    cfg = load_config()
    return jsonify({"success": True, "config": {
        "smtp_email": cfg.get("smtp_email", ""),
        "sender_name": cfg.get("sender_name", ""),
        "has_password": bool(cfg.get("smtp_password", "")),
    }})


@email_bp.route("/api/email/smtp_settings", methods=["POST"])
@rate_limit(max_requests=10, window=300)
@login_required
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
@rate_limit(max_requests=5, window=300)
@login_required
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


# ============================================================
# 两阶段邮件确认发送
# ============================================================
@email_bp.route("/api/email/draft", methods=["POST"])
@rate_limit(max_requests=30, window=300)
@login_required
def api_create_draft():
    """生成邮件草稿（不发送）。返回 draft_id 供用户确认后发送。"""
    data = request.get_json() or {}
    to_email = _safe_str(data.get("to_email")).strip()
    subject = _safe_str(data.get("subject")).strip()
    body = _safe_str(data.get("body")).strip()
    to_name = _safe_str(data.get("to_name")).strip()

    if not to_email or not subject or not body:
        return jsonify({"success": False, "error": "缺少必要参数：to_email, subject, body"}), 400

    draft_id = uuid.uuid4().hex
    db.kv_set(f"email_draft:{draft_id}", {
        "to_email": to_email,
        "subject": subject,
        "body": body,
        "to_name": to_name,
        "user_email": g.user_email,
        "created_at": db._now(),
    })

    return jsonify({
        "success": True,
        "draft_id": draft_id,
        "preview": {"to_email": to_email, "subject": subject, "body": body, "to_name": to_name},
        "message": "草稿已生成，请在前端确认后发送",
    })


@email_bp.route("/api/email/draft/<draft_id>/send", methods=["POST"])
@rate_limit(max_requests=10, window=300)
@login_required
def api_send_draft(draft_id):
    """确认并发送邮件草稿。需 idempotency_key 防止重复发送。"""
    data = request.get_json() or {}
    idempotency_key = _safe_str(data.get("idempotency_key")).strip()

    if not idempotency_key:
        return jsonify({"success": False, "error": "缺少 idempotency_key（用于防重复发送）"}), 400

    # 检查重复发送
    if db.kv_get(f"idempotency:{idempotency_key}"):
        return jsonify({"success": False, "error": "该邮件已发送，请勿重复操作"}), 409

    draft = db.kv_get(f"email_draft:{draft_id}")
    if not draft:
        return jsonify({"success": False, "error": "草稿不存在或已过期"}), 404

    if draft["user_email"] != g.user_email:
        return jsonify({"success": False, "error": "无权操作此草稿"}), 403

    if not mailer.is_configured():
        return jsonify({"success": False, "error": "SMTP 未配置。请在页面设置中填写邮箱信息"}), 400

    # 检查收件人是否已退订
    to_email = draft.get("to_email", "")
    if db.is_unsubscribed(to_email):
        return jsonify({"success": False, "error": f"收件人 {to_email} 已退订，无法发送"}), 400

    # 检查每日发送配额（每用户每天最多 50 封）
    today_prefix = f"email_audit:{datetime.utcnow().strftime('%Y%m%d')}"
    daily_count = sum(1 for log in db.get_email_audit_logs(user_email=g.user_email, limit=100)
                      if log.get("success"))
    if daily_count >= 50:
        return jsonify({
            "success": False,
            "error": "今日发送已达上限 (50封/天)，请明天再试",
            "daily_limit": 50,
            "retry_after": "明天 00:00",
        }), 429

    # 检查邮箱是否已通过验证（未被推测的邮箱才允许直接发送）
    guessed_patterns = ["purchasing@", "info@", "sales@", "inquiry@", "procurement@",
                       "import@", "export@", "contact@", "admin@", "office@"]
    to_email_lower = to_email.lower()
    is_guessed = any(to_email_lower.startswith(p) for p in guessed_patterns)
    if is_guessed and not data.get("confirm_unverified"):
        return jsonify({
            "success": False,
            "error": "此邮箱疑似基于域名推测生成，尚未验证有效性，直接发送可能导致退信或标记为垃圾邮件。请先验证邮箱有效后再发送。",
            "require_confirmation": True,
            "hint": "建议使用 Hunter.io / FindThatLead / Snov.io 验证邮箱有效性，或确认后添加 confirm_unverified: true 强制发送",
        }), 422

    # 发送前审计日志
    db.log_email_audit(draft_id, g.user_email, to_email, draft.get("subject", ""),
                       draft.get("body", ""), idempotency_key, False)

    # 先标记幂等键（防竞态）
    db.kv_set(f"idempotency:{idempotency_key}", {
        "draft_id": draft_id, "sent_at": db._now()
    })

    result = mailer.send_email_smtp(
        to_email=to_email, subject=draft["subject"],
        body=draft["body"], to_name=draft["to_name"], from_name="")
    if result.get("success"):
        eid, tid = track_sent_email(g.user_email, to_email, draft["to_name"],
                                     draft["subject"], draft["body"])
        result["tracking_id"] = tid
        db.kv_delete(f"email_draft:{draft_id}")

    # 发送后审计日志
    db.log_email_audit(draft_id, g.user_email, to_email, draft.get("subject", ""),
                       draft.get("body", ""), idempotency_key,
                       result.get("success", False), result.get("error"))

    return jsonify(result)


@email_bp.route("/api/email/unsubscribe/<token>", methods=["GET"])
def api_unsubscribe(token):
    """退订端点（公开，基于 HMAC token 验证）"""
    import hmac
    try:
        import base64
        decoded = base64.urlsafe_b64decode(token.encode() + b"==").decode()
        parts = decoded.split("|")
        if len(parts) != 2:
            return "<h3>无效的退订链接</h3>", 400
        email_addr, sig = parts
        expected = hmac.new(
            __import__('config').SECRET_KEY.encode(),
            email_addr.encode(), "sha256"
        ).hexdigest()[:16]
        if not hmac.compare_digest(sig, expected):
            return "<h3>无效的退订链接</h3>", 400

        if db.is_unsubscribed(email_addr):
            return "<h3>该邮箱已经退订</h3>", 200

        db.add_unsubscribe(email_addr, reason="用户点击退订链接")
        return f"<h3>{email_addr} 已成功退订，将不再收到来自 TradeMaster 的邮件</h3>", 200
    except Exception:
        return "<h3>无效的退订链接</h3>", 400


def generate_unsubscribe_token(email):
    """生成退订 token（用于邮件中嵌入 List-Unsubscribe 链接）"""
    import hmac
    import base64
    sig = hmac.new(
        __import__('config').SECRET_KEY.encode(),
        email.encode(), "sha256"
    ).hexdigest()[:16]
    payload = base64.urlsafe_b64encode(f"{email}|{sig}".encode()).decode().rstrip("=")
    return payload
