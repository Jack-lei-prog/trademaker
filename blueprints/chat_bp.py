"""聊天 Blueprint — /api/chat, /api/chat/stream, /api/clear, /"""
from flask import Blueprint, render_template, request, jsonify, Response
from security import rate_limit
from services import _safe_str, _needs_tools, run_agent, run_agent_stream
import db
import json

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/")
def index():
    return render_template("index.html")


@chat_bp.route("/api/chat", methods=["POST"])
@rate_limit(max_requests=30, window=60)
def chat():
    data = request.get_json()
    user_input = _safe_str(data.get("message")).strip()
    user_email = _safe_str(data.get("user_email")).strip().lower()
    session_id = user_email or _safe_str(data.get("session_id")) or "default"

    if not user_input:
        return jsonify({"error": "请输入消息"}), 400

    if user_input.lower() in ("quit", "exit", "q", "退出"):
        return jsonify({"reply": "感谢使用外贸通，再见！👋", "tool_calls": []})

    if user_input.lower() in ("help", "h", "帮助"):
        return jsonify({"reply": get_help_text(), "tool_calls": []})

    if user_input.lower() in ("clear", "清空", "新会话"):
        db.delete_session(user_email, session_id)
        return jsonify({"reply": "会话已清空，我们可以开始新的对话了！", "tool_calls": []})

    result = run_agent(user_input, session_id, use_tools=_needs_tools(user_input), user_email=user_email)
    return jsonify(result)


@chat_bp.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    data = request.get_json()
    user_input = _safe_str(data.get("message")).strip()
    user_email = _safe_str(data.get("user_email")).strip().lower()
    session_id = user_email or _safe_str(data.get("session_id")) or "default"

    if not user_input:
        def eg(): yield "data: {\"type\":\"error\",\"message\":\"请输入消息\"}\n\n"
        return Response(eg(), mimetype="text/event-stream")

    if user_input.lower() in ("quit", "exit", "q", "退出"):
        def qg():
            yield f"data: {json.dumps({'type': 'text', 'content': '感谢使用外贸通，再见！👋'}, ensure_ascii=False)}\n\n"
            yield "data: {\"type\":\"done\"}\n\n"
        return Response(qg(), mimetype="text/event-stream")

    if user_input.lower() in ("help", "h", "帮助"):
        help_text = get_help_text()
        def hg():
            yield f"data: {json.dumps({'type': 'text', 'content': help_text}, ensure_ascii=False)}\n\n"
            yield "data: {\"type\":\"done\"}\n\n"
        return Response(hg(), mimetype="text/event-stream")

    if user_input.lower() in ("clear", "清空", "新会话"):
        db.delete_session(user_email, session_id)
        def cg():
            yield f"data: {json.dumps({'type': 'text', 'content': '会话已清空！'}, ensure_ascii=False)}\n\n"
            yield "data: {\"type\":\"done\"}\n\n"
        return Response(cg(), mimetype="text/event-stream")

    def generate():
        for event in run_agent_stream(user_input, session_id, use_tools=_needs_tools(user_input), user_email=user_email):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "data: {\"type\":\"done\"}\n\n"
    return Response(generate(), mimetype="text/event-stream")


@chat_bp.route("/api/clear", methods=["POST"])
def clear_chat():
    data = request.get_json() or {}
    session_id = _safe_str(data.get("session_id")) or "default"
    user_email = _safe_str(data.get("user_email"))
    db.delete_session(user_email=user_email, session_id=session_id)
    return jsonify({"success": True})


@chat_bp.route("/api/health", methods=["GET"])
def health():
    """健康检查：数据库状态、API 连通性、运行时间"""
    import time as _t
    import os as _os
    status = {"status": "ok", "service": "TradeMaster", "version": "2.1.0"}
    checks = {}

    # 数据库检查
    try:
        db.get_or_create_session("health_check", "health")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:100]}"
        status["status"] = "degraded"

    # API 连通性检查
    from services import get_provider_status, LLM_PROVIDERS
    checks["llm_api"] = {
        "providers": len(LLM_PROVIDERS),
        "detail": {p["name"]: get_provider_status().get(p["name"], {}).get("status", "unknown")
                   for p in LLM_PROVIDERS}
    }

    # 磁盘检查
    try:
        stat = _os.statvfs(".") if hasattr(_os, "statvfs") else None
        if stat:
            free_mb = stat.f_frsize * stat.f_bavail / (1024 * 1024)
            checks["disk_free_mb"] = round(free_mb, 1)
    except Exception:
        pass

    status["checks"] = checks
    status["timestamp"] = _t.strftime("%Y-%m-%d %H:%M:%S", _t.localtime())
    return jsonify(status)


@chat_bp.route("/api/demo/help", methods=["GET"])
def demo_help():
    """返回演示指南"""
    from knowledge.demo import DEMO_HELP, DEMO_SCENARIOS
    return jsonify({
        "success": True,
        "demo_account": {"email": "demo@trademaster.com", "password": "demo2024"},
        "scenarios": DEMO_SCENARIOS,
        "help_text": DEMO_HELP,
    })


@chat_bp.route("/api/docs", methods=["GET"])
def api_docs():
    """API 文档页面"""
    docs = {
        "service": "TradeMaster 外贸通",
        "version": "2.1.0",
        "architecture": "单Agent + 12 Skill协同 (Function Calling) + RAG知识检索",
        "endpoints": [
            {"method": "POST", "path": "/api/register", "desc": "用户注册", "auth": False},
            {"method": "POST", "path": "/api/login", "desc": "用户登录", "auth": False},
            {"method": "POST", "path": "/api/chat", "desc": "AI对话 (同步)", "auth": False, "stream": False},
            {"method": "POST", "path": "/api/chat/stream", "desc": "AI对话 (SSE流式)", "auth": False, "stream": True},
            {"method": "POST", "path": "/api/clear", "desc": "清空会话", "auth": False},
            {"method": "GET", "path": "/api/health", "desc": "健康检查+API状态", "auth": False},
            {"method": "GET", "path": "/api/docs", "desc": "本API文档", "auth": False},
            {"method": "GET", "path": "/api/demo/help", "desc": "演示指南", "auth": False},
            {"method": "POST", "path": "/api/dashboard", "desc": "仪表盘数据", "auth": True},
            {"method": "POST", "path": "/api/send_email", "desc": "生成邮件发送界面", "auth": False},
            {"method": "POST", "path": "/api/email/smtp_send", "desc": "SMTP发送邮件", "auth": False},
            {"method": "POST", "path": "/api/email/stats", "desc": "邮件统计", "auth": True},
            {"method": "POST", "path": "/api/emails/sent", "desc": "已发送邮件列表", "auth": True},
            {"method": "POST", "path": "/api/emails/pending", "desc": "待跟进邮件", "auth": True},
            {"method": "POST", "path": "/api/contacts/add", "desc": "添加待联系客户", "auth": True},
            {"method": "POST", "path": "/api/contacts/list", "desc": "客户列表", "auth": True},
            {"method": "POST", "path": "/api/contacts/update", "desc": "更新客户状态", "auth": True},
            {"method": "POST", "path": "/api/contacts/stats", "desc": "客户统计", "auth": True},
            {"method": "POST", "path": "/api/inquiry/process", "desc": "询盘处理", "auth": False},
            {"method": "POST", "path": "/api/evaluate", "desc": "评价回答质量", "auth": False},
            {"method": "POST", "path": "/api/evaluate/kimi", "desc": "Kimi深度评价", "auth": False},
        ],
        "skills": [
            "buyer_search — 买家搜索 (Wikidata/OpenCorp/LLM)",
            "email_draft — 开发信撰写 (B2B模板+企业拦截)",
            "trade_intelligence — 展会情报 (50+展会+认证+术语)",
            "inquiry_processing — 询盘处理 (5步闭环)",
            "email_tracking — 邮件追踪 (像素+退信检测)",
            "contact_management — 客户管理 (7状态Pipeline)",
        ],
        "knowledge_base": {
            "tradeshows": "50+全球展会数据库，按产品匹配",
            "certifications": "CE/FCC/RoHS/BQB等出口认证清单",
            "trade_terms": "18个外贸术语 (FOB/CIF/MOQ/OEM等)",
            "rag_search": "TF-IDF语义检索，/api/chat自动调用"
        }
    }
    return jsonify(docs)


def get_help_text():
    return """## 📖 使用帮助
我可以帮您完成以下任务：
1. **🔍 买家搜索** — "帮我搜索电子产品相关的买家"
2. **📊 公司分析** — "分析一下 techglobal.com 这家公司"
3. **✉️ 开发信撰写** — "给 TechGlobal 写一封开发信，推销蓝牙耳机"
4. **📩 询盘处理** — 直接粘贴客户询盘邮件内容
5. **💱 汇率查询** — "美元兑人民币的汇率是多少？"
6. **📝 商品描述生成** — "帮我为便携式加湿器生成商品描述"
7. **💬 客户回复起草** — "客户问快递到哪了"
8. **📈 销售日报分析** — "分析今天的销售数据"
9. **🎯 营销广告语生成** — "为夏日防晒衣生成广告语"
请直接输入您的需求，我会尽力帮助您！"""
