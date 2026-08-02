# -*- coding: utf-8 -*-
"""
外贸通 Web 应用
基于 Flask 的 Web 界面，提供聊天功能
"""
import os
import json
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT
from tools import TOOL_FUNCTIONS, TOOL_DESCRIPTIONS
from evaluator import evaluate_response

load_dotenv()

app = Flask(__name__)

# ============================================================
# 用户系统 — JSON 文件存储
# ============================================================
USERS_FILE = "users.json"


def _load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def get_user(email):
    """根据邮箱查找用户，返回用户字典或 None"""
    return _load_users().get(email.lower().strip())


def build_system_prompt(email=None):
    """构建包含用户信息的系统提示词"""
    user = get_user(email) if email else None
    if not user:
        return SYSTEM_PROMPT

    identity = user.get("identity", "seller")

    extra = f"""
# 当前用户信息
- 账号邮箱：{user['email']}
- 联系电话：{user.get('phone', '未填写')}
- 公司名称：{user.get('company', '未填写')}
- 主营产品：{user.get('product', '未填写')}
- 使用身份：{'老板/管理者' if identity == 'boss' else '销售业务员'}

# 重要指令
- 开发信和邮件中，发件人邮箱用 {user['email']}，公司名用 {user.get('company', '我司')}，不要用 [Your Email] 或 [Your Company] 等占位符
- 电话署名用 {user.get('phone', '')}
"""

    if identity == 'boss':
        extra += """
# 老板模式
- 侧重整体数据和趋势分析
- 关注销售报表、团队绩效、市场机会
- 回复风格简洁高效，给决策建议"""
    else:
        extra += f"""
# 销售模式
- 侧重开发信撰写、买家搜索、客户跟进
- 主营产品是 {user.get('product', '')}，主动围绕该产品寻找买家
- 回复风格热情专业，帮助业务员完成销售任务"""

    return SYSTEM_PROMPT + "\n" + extra

# HTTP Session 复用连接
http_session = requests.Session()

# API 配置
SYNSCALE_API_KEY = os.getenv("SYNSCALE_API_KEY")
SYNSCALE_API_URL = "http://synscale.onesyn.ai/v1/chat/completions"
MODEL_NAME = os.getenv("SYNSCALE_MODEL_NAME", "deepseek-v4-pro")
MAX_ITERATIONS = 2

# 工具中文名称映射（前端展示用）
TOOL_LABELS = {
    "search_buyers": ("🔍 AI 买家搜索", "正在从全球贸易数据库搜索潜在买家..."),
    "analyze_company": ("📊 分析公司背景", "正在查询公司注册信息..."),
    "draft_email": ("✉️ 生成开发信", "正在撰写英文开发信..."),
    "send_email": ("📧 准备发送邮件", "正在生成邮件..."),
    "check_email_status": ("📬 检查邮件状态", "正在检查已发送邮件的跟进状态..."),
    "query_exchange_rate": ("💱 查询汇率", "正在获取实时汇率..."),
    "generate_product_desc": ("📝 生成商品描述", "正在撰写商品文案..."),
    "draft_customer_reply": ("💬 起草客户回复", "正在生成客服回复..."),
    "analyze_daily_sales": ("📈 分析销售数据", "正在生成销售日报..."),
    "write_marketing_slogan": ("🎯 生成广告语", "正在创作营销文案..."),
}

# 存储会话历史（简单实现，生产环境应使用数据库）
chat_history = {}

# ============================================================
# 邮件跟踪系统
# ============================================================
EMAILS_FILE = "emails_sent.json"


def _load_emails():
    if not os.path.exists(EMAILS_FILE):
        return {}
    try:
        with open(EMAILS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_emails(emails):
    with open(EMAILS_FILE, 'w', encoding='utf-8') as f:
        json.dump(emails, f, ensure_ascii=False, indent=2)


def track_sent_email(user_email, to_email, to_name, subject, body):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    eid = f"{user_email}_{to_email}_{now.replace(' ', '_').replace(':', '-')}"
    emails = _load_emails()
    emails[eid] = {
        "id": eid, "from": user_email, "to": to_email,
        "to_name": to_name, "subject": subject,
        "body_preview": body[:200], "sent_at": now,
        "status": "sent", "followups": [],
    }
    _save_emails(emails)
    return eid


def get_user_emails(user_email):
    return [v for v in _load_emails().values() if v["from"] == user_email]


def get_pending_followups(user_email):
    from datetime import timedelta
    now = datetime.now()
    pending = []
    for e in get_user_emails(user_email):
        if e["status"] in ("sent", "no_reply"):
            days = (now - datetime.strptime(e["sent_at"], "%Y-%m-%d %H:%M")).days
            if days >= 1:
                pending.append({**e, "days_ago": days})
    return pending


def update_email_status(user_email, to_email, new_status):
    emails = _load_emails()
    for k, v in emails.items():
        if v["from"] == user_email and v["to"] == to_email:
            v["status"] = new_status
            _save_emails(emails)
            return v
    return None


@app.route('/api/emails/sent', methods=['POST'])
def api_get_sent_emails():
    """获取用户已发送的所有邮件"""
    data = request.get_json() or {}
    email = data.get('user_email', '').strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Missing user_email"}), 400
    return jsonify({"success": True, "emails": get_user_emails(email)})


@app.route('/api/emails/pending', methods=['POST'])
def api_pending_followups():
    data = request.get_json() or {}
    email = data.get('user_email', '').strip().lower()
    pending = get_pending_followups(email)
    return jsonify({"success": True, "pending": pending,
                    "count": len(pending)})


@app.route('/api/emails/status', methods=['POST'])
def api_update_email_status():
    data = request.get_json() or {}
    ue, te, st = data.get('user_email','').lower(), data.get('to_email','').lower(), data.get('status','').lower()
    if not ue or not te or st not in ('sent','replied','bounced','no_reply'):
        return jsonify({"success": False, "error": "Invalid"}), 400
    r = update_email_status(ue, te, st)
    return jsonify({"success": True, "email": r} if r else {"success": False, "error": "Not found"})

# 简单问题关键词，不需要调用 tools
SIMPLE_QUERIES = {
    '你好', 'hello', 'hi', 'hey', '谢谢', 'thank', '你是谁', 'what are you',
    '再见', 'bye', 'goodbye', '晚安', '早上好', '晚上好', 'good morning',
    'good evening', 'good night', '介绍', 'introduce',
}


def _needs_tools(user_input):
    """判断用户输入是否需要调用工具"""
    lower = user_input.lower().strip()
    for kw in SIMPLE_QUERIES:
        if kw in lower:
            return False
    return True


def call_synscale(messages, tools=None):
    """调用 SynScale API"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SYNSCALE_API_KEY}"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 2000
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    else:
        payload["temperature"] = 0.4
        payload["max_tokens"] = 800

    try:
        response = http_session.post(SYNSCALE_API_URL, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": True, "message": f"API Error: {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": True, "message": f"Request failed: {str(e)}"}


def execute_tool(tool_name, tool_args):
    """执行工具函数"""
    if tool_name not in TOOL_FUNCTIONS:
        return json.dumps({"error": True, "message": f"Unknown tool: {tool_name}"}, ensure_ascii=False)
    try:
        tool_func = TOOL_FUNCTIONS[tool_name]
        result = tool_func(**tool_args)
        return result
    except Exception as e:
        return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


def run_agent(user_input, session_id="default", use_tools=True, user_email=None):
    """运行 Agent 处理用户输入"""
    # 获取或初始化会话历史
    if session_id not in chat_history:
        chat_history[session_id] = [
            {"role": "system", "content": build_system_prompt(user_email)}
        ]

    messages = chat_history[session_id]
    messages.append({"role": "user", "content": user_input})

    iteration = 0
    tool_calls_log = []

    while iteration < MAX_ITERATIONS:
        iteration += 1

        response = call_synscale(messages, tools=TOOL_DESCRIPTIONS if use_tools else None)

        if "error" in response:
            error_msg = f"抱歉，发生了错误：{response.get('message', 'Unknown error')}"
            messages.append({"role": "assistant", "content": error_msg})
            return {"reply": error_msg, "tool_calls": tool_calls_log}

        choices = response.get("choices", [])
        if not choices:
            error_msg = "抱歉，未能获取回复"
            messages.append({"role": "assistant", "content": error_msg})
            return {"reply": error_msg, "tool_calls": tool_calls_log}

        message = choices[0].get("message", {})
        assistant_content = message.get("content", "")
        tool_calls = message.get("tool_calls", [])

        if tool_calls:
            # 记录工具调用
            messages.append({
                "role": "assistant",
                "content": assistant_content,
                "tool_calls": tool_calls
            })

            for tool_call in tool_calls:
                function_info = tool_call.get("function", {})
                tool_name = function_info.get("name", "")
                tool_args_str = function_info.get("arguments", "{}")
                tool_call_id = tool_call.get("id", "")

                try:
                    tool_args = json.loads(tool_args_str)
                except json.JSONDecodeError:
                    tool_args = {}

                # 执行工具
                tool_result = execute_tool(tool_name, tool_args)
                # Safe JSON parsing - some tools return plain text (e.g. draft_email)
                try:
                    parsed_result = json.loads(tool_result) if isinstance(tool_result, str) else tool_result
                except (json.JSONDecodeError, TypeError):
                    parsed_result = tool_result
                tool_calls_log.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": parsed_result
                })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": tool_result
                })
        else:
            # 最终回复
            messages.append({"role": "assistant", "content": assistant_content})
            # 保持会话历史在合理长度
            if len(messages) > 15:
                chat_history[session_id] = [messages[0]] + messages[-10:]
            return {"reply": assistant_content, "tool_calls": tool_calls_log}

    timeout_msg = "抱歉，处理超时，请简化您的问题后重试"
    messages.append({"role": "assistant", "content": timeout_msg})
    return {"reply": timeout_msg, "tool_calls": tool_calls_log}


def call_synscale_stream(messages, tools=None):
    """流式调用 SynScale API，yield 每个 delta chunk"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SYNSCALE_API_KEY}"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 2000,
        "stream": True
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    else:
        payload["temperature"] = 0.4
        payload["max_tokens"] = 800

    try:
        response = http_session.post(SYNSCALE_API_URL, headers=headers, json=payload, timeout=10, stream=True)
        if response.status_code != 200:
            yield {"error": True, "message": f"API Error: {response.status_code}", "details": response.text}
            return

        for line in response.iter_lines():
            if not line:
                continue
            line_str = line.decode("utf-8", errors="replace")
            if line_str.startswith("data: "):
                data_str = line_str[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    yield delta
    except Exception as e:
        yield {"error": True, "message": f"Request failed: {str(e)}"}


def run_agent_stream(user_input, session_id="default", use_tools=True, user_email=None):
    """流式 Agent 循环，yield SSE 事件字典（含思考过程）"""
    # 获取或初始化会话历史
    if session_id not in chat_history:
        chat_history[session_id] = [
            {"role": "system", "content": build_system_prompt(user_email)}
        ]

    messages = chat_history[session_id]
    messages.append({"role": "user", "content": user_input})

    iteration = 0
    total_tool_count = 0

    # 发送"开始思考"事件
    yield {"type": "thinking", "message": "正在理解您的问题..."}

    while iteration < MAX_ITERATIONS:
        iteration += 1

        # 累积流式回复
        full_content = ""
        tool_call_chunks = {}  # {index: {id, name, arguments_str}}

        for delta in call_synscale_stream(messages, tools=TOOL_DESCRIPTIONS if use_tools else None):
            if "error" in delta:
                yield {"type": "error", "message": delta.get("message", "Unknown error")}
                return

            content = delta.get("content", "")
            tc_deltas = delta.get("tool_calls", [])

            if content:
                full_content += content
                yield {"type": "text", "content": content}

            for tc in tc_deltas:
                idx = tc.get("index", 0)
                if idx not in tool_call_chunks:
                    tool_call_chunks[idx] = {"id": "", "name": "", "arguments": ""}

                if "id" in tc and tc["id"]:
                    tool_call_chunks[idx]["id"] = tc["id"]

                func = tc.get("function", {})
                if "name" in func and func["name"]:
                    tool_call_chunks[idx]["name"] = func["name"]

                if "arguments" in func:
                    tool_call_chunks[idx]["arguments"] += func["arguments"]

        # 处理 tool_calls
        if tool_call_chunks:
            tool_calls = []
            for idx in sorted(tool_call_chunks.keys()):
                tc = tool_call_chunks[idx]
                tool_calls.append(tc)

            # 构建 assistant message
            assistant_msg = {"role": "assistant", "content": full_content}
            api_tool_calls = []
            for tc in tool_calls:
                api_tool_calls.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"]
                    }
                })
            assistant_msg["tool_calls"] = api_tool_calls
            messages.append(assistant_msg)

            # 执行每个 tool_call
            for i, tc in enumerate(tool_calls):
                tool_name = tc["name"]
                try:
                    tool_args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    tool_args = {}

                label, detail = TOOL_LABELS.get(tool_name, (tool_name, f"正在调用 {tool_name}..."))
                total_tool_count += 1

                # 发送 tool_call 事件（含中文标签）
                yield {
                    "type": "tool_call",
                    "tool": tool_name,
                    "label": label,
                    "detail": detail,
                    "args": tool_args,
                    "step": total_tool_count,
                    "total_steps": len(tool_calls),
                    "round": iteration
                }

                # 执行工具
                tool_result = execute_tool(tool_name, tool_args)

                # 发送邮件后自动记录跟踪
                if tool_name == "send_email" and user_email:
                    try:
                        track_sent_email(
                            user_email=user_email,
                            to_email=tool_args.get("to_email", ""),
                            to_name=tool_args.get("to_name", ""),
                            subject=tool_args.get("subject", ""),
                            body=tool_args.get("body", "")
                        )
                    except Exception:
                        pass

                # 解析结果
                try:
                    parsed_result = json.loads(tool_result) if isinstance(tool_result, str) else tool_result
                except (json.JSONDecodeError, TypeError):
                    parsed_result = tool_result

                # 提取结果摘要
                summary = _extract_result_summary(tool_name, parsed_result)

                # 发送 tool_result 事件（含结果摘要）
                yield {
                    "type": "tool_result",
                    "tool": tool_name,
                    "label": label,
                    "result": parsed_result,
                    "summary": summary,
                    "step": total_tool_count,
                    "total_steps": len(tool_calls),
                    "round": iteration
                }

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": tool_result
                })

            # 有下一轮：发送思考事件
            if iteration < MAX_ITERATIONS:
                yield {"type": "thinking", "message": "正在综合信息生成回复..."}
        else:
            # 无 tool_call，最终回复 → GAN 评价循环
            messages.append({"role": "assistant", "content": full_content})
            if len(messages) > 15:
                chat_history[session_id] = [messages[0]] + messages[-10:]

            # 完成回答
            messages.append({"role": "assistant", "content": full_content})
            if len(messages) > 15:
                chat_history[session_id] = [messages[0]] + messages[-10:]
            return

    yield {"type": "error", "message": "处理超时，请简化问题后重试"}


def _extract_result_summary(tool_name, result):
    """从工具结果中提取简短摘要"""
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return result[:120] if len(result) > 120 else result

    if not isinstance(result, dict):
        return str(result)[:120]

    if tool_name == "search_buyers":
        count = result.get("total_count", 0)
        source = result.get("source", "unknown")
        buyers = result.get("buyers", [])
        if count == 0:
            return "未找到匹配的买家，请尝试更具体的英文关键词"
        names = []
        for b in buyers[:5]:
            name = b.get("company_name", "")
            country = b.get("country", "")
            btype = b.get("buyer_type", "")
            if name:
                tag = f"[{btype}]" if btype else ""
                loc = f"({country})" if country else ""
                names.append(f"{name} {tag}{loc}")
        preview = " | ".join(names) if names else ""
        return f"✅ 找到 {count} 家潜在买家（来源：{source}）\n{preview}{'...' if count > 5 else ''}"

    elif tool_name == "analyze_company":
        if result.get("success"):
            info = result.get("company_info", {})
            name = info.get("company_name", result.get("domain", "?"))
            status = info.get("status", "?")
            return f"✅ {name} — 状态：{status}"
        return f"❌ {result.get('error', '未知错误')}"

    elif tool_name == "query_exchange_rate":
        if result.get("success"):
            rate = result.get("rate_to_cny", "?")
            cur = result.get("currency", "?")
            return f"1 {cur} = {rate} CNY"
        return f"❌ {result.get('error', '查询失败')}"

    elif tool_name in ("draft_email", "generate_product_desc", "draft_customer_reply", "write_marketing_slogan"):
        if isinstance(result, str) and len(result) > 80:
            return result[:80] + "..."
        return "生成完成"

    elif tool_name == "analyze_daily_sales":
        total = result.get("total_orders", 0)
        income = result.get("total_income", 0)
        top = result.get("top_products", [])
        top_name = top[0].get("name", "") if top else ""
        return f"共{total}单，收入{income}元，热销：{top_name}"

    elif tool_name == "send_email":
        if result.get("success"):
            return f"📧 邮件已准备就绪，收件人：{result.get('to_email', '?')}"
        return f"❌ {result.get('error', '发送失败')}"

    return "操作完成"


@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    company = data.get('company', '').strip()
    product = data.get('product', '').strip()
    identity = data.get('identity', 'seller')

    # 验证
    if not email or '@' not in email:
        return jsonify({"success": False, "error": "请输入有效的邮箱地址"}), 400
    if not phone:
        return jsonify({"success": False, "error": "请输入联系电话"}), 400
    if not product:
        return jsonify({"success": False, "error": "请输入主营产品"}), 400
    if identity not in ('seller', 'boss'):
        identity = 'seller'

    users = _load_users()
    if email in users:
        return jsonify({"success": False, "error": "该邮箱已注册，请直接登录"}), 400

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    user = {
        "email": email,
        "phone": phone,
        "company": company,
        "product": product,
        "identity": identity,
        "registered_at": now,
        "last_login": now,
    }
    users[email] = user
    _save_users(users)

    return jsonify({"success": True, "user": user})


@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({"success": False, "error": "请输入邮箱地址"}), 400

    user = get_user(email)
    if not user:
        return jsonify({"success": False, "error": "未找到该用户，请先注册"}), 404

    user['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    users = _load_users()
    users[email] = user
    _save_users(users)

    return jsonify({"success": True, "user": user})


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/send_email', methods=['POST'])
def api_send_email():
    """直接发送邮件 API（前端调用）"""
    data = request.get_json()
    to_email = data.get('to_email', '').strip()
    subject = data.get('subject', '').strip()
    body = data.get('body', '').strip()
    to_name = data.get('to_name', '').strip()

    if not to_email or not subject or not body:
        return jsonify({"success": False, "error": "缺少必要参数：to_email, subject, body"}), 400

    result = execute_tool("send_email", {
        "to_email": to_email,
        "subject": subject,
        "body": body,
        "to_name": to_name
    })

    try:
        parsed = json.loads(result) if isinstance(result, str) else result
        return jsonify(parsed)
    except (json.JSONDecodeError, TypeError):
        return jsonify({"success": False, "error": str(result)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天 API"""
    data = request.get_json()
    user_input = data.get('message', '').strip()
    user_email = data.get('user_email', '').strip().lower()
    session_id = user_email or data.get('session_id', 'default')

    if not user_input:
        return jsonify({"error": "请输入消息"}), 400

    # 处理特殊命令
    if user_input.lower() in ['quit', 'exit', 'q', '退出']:
        return jsonify({"reply": "感谢使用外贸通，再见！👋", "tool_calls": []})

    if user_input.lower() in ['help', 'h', '帮助']:
        help_text = """## 📖 使用帮助

我可以帮您完成以下任务：

1. **🔍 买家搜索** - 根据关键词搜索潜在买家
   - 示例："帮我搜索电子产品相关的买家"

2. **📊 公司分析** - 分析指定公司的背景信息
   - 示例："分析一下 techglobal.com 这家公司"

3. **✉️ 开发信撰写** - 根据客户信息生成开发信
   - 示例："给 TechGlobal 写一封开发信，推销蓝牙耳机"

4. **💱 汇率查询** - 查询货币汇率
   - 示例："美元兑人民币的汇率是多少？"

5. **📝 商品描述生成** - 生成商品标题、卖点和描述
   - 示例："帮我为便携式加湿器生成商品描述"

6. **💬 客户回复起草** - 根据客户消息生成回复
   - 示例："客户问快递到哪了，帮我起草回复"

7. **📈 销售日报分析** - 分析销售数据生成日报
   - 示例："分析今天的销售数据：保温杯20个，手机支架35个"

8. **🎯 营销广告语生成** - 根据主题生成广告语
   - 示例："为夏日防晒衣生成几条广告语"

请直接输入您的需求，我会尽力帮助您！"""
        return jsonify({"reply": help_text, "tool_calls": []})

    if user_input.lower() in ['clear', '清空', '新会话']:
        if session_id in chat_history:
            del chat_history[session_id]
        return jsonify({"reply": "会话已清空，我们可以开始新的对话了！", "tool_calls": []})

    needs_tools = _needs_tools(user_input)
    result = run_agent(user_input, session_id, use_tools=needs_tools, user_email=user_email)
    return jsonify(result)


@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    """GAN 评价 + 改进端点"""
    data = request.get_json()
    user_question = data.get('question', '').strip()
    agent_answer = data.get('answer', '').strip()

    if not user_question or not agent_answer:
        return jsonify({"success": False, "error": "需要 question 和 answer"}), 400

    evaluation = evaluate_response(user_question, agent_answer)
    if not evaluation:
        return jsonify({"success": False, "error": "评价服务暂不可用"}), 503

    return jsonify({"success": True, "evaluation": evaluation})


@app.route('/api/evaluate/improve', methods=['POST'])
def evaluate_improve():
    """GAN 评价 + 改进：返回改进后的回答（SSE流式）"""
    data = request.get_json()
    user_question = data.get('question', '').strip()
    agent_answer = data.get('answer', '').strip()
    session_id = data.get('session_id', 'default')
    user_email = data.get('user_email', '')

    if not user_question or not agent_answer:
        return jsonify({"success": False, "error": "需要 question 和 answer"}), 400

    # Step 1: evaluate
    evaluation = evaluate_response(user_question, agent_answer)
    if not evaluation:
        def err_gen():
            yield "data: {\"type\":\"error\",\"message\":\"评价服务暂不可用\"}\n\n"
        return Response(err_gen(), mimetype="text/event-stream")

    # Step 2: send evaluation
    def generate():
        yield f"data: {json.dumps({'type': 'evaluation', 'scores': evaluation.get('scores', {}), 'strengths': evaluation.get('strengths', []), 'weaknesses': evaluation.get('weaknesses', []), 'suggestion': evaluation.get('suggestion', '')}, ensure_ascii=False)}\n\n"

        overall = float(evaluation.get("scores", {}).get("overall", 0) or 0)
        if evaluation.get("need_improve") and overall < 8.0:
            feedback = (
                f"你的上一轮回答得到了{overall:.1f}分（满分10分）。\n"
                f"优点：{'; '.join(evaluation.get('strengths', []))}\n"
                f"缺点：{'; '.join(evaluation.get('weaknesses', []))}\n"
                f"改进建议：{evaluation.get('suggestion', '请改进回答质量')}\n\n"
                f"请基于以上反馈，重新回答用户的原始问题：{user_question}"
            )

            # Build messages for improvement
            msgs = [{"role": "user", "content": user_question},
                    {"role": "assistant", "content": agent_answer},
                    {"role": "user", "content": feedback}]

            for delta in call_synscale_stream(msgs, tools=None):
                if "error" in delta:
                    break
                c = delta.get("content", "")
                if c:
                    yield f"data: {json.dumps({'type': 'text_improved', 'content': c}, ensure_ascii=False)}\n\n"

        yield "data: {\"type\":\"done\"}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """流式聊天 API (SSE)"""
    data = request.get_json()
    user_input = data.get('message', '').strip()
    user_email = data.get('user_email', '').strip().lower()
    session_id = user_email or data.get('session_id', 'default')

    if not user_input:
        def err_gen():
            yield "data: {\"type\":\"error\",\"message\":\"请输入消息\"}\n\n"
        return Response(err_gen(), mimetype="text/event-stream")

    # 特殊命令处理
    if user_input.lower() in ['quit', 'exit', 'q', '退出']:
        def quit_gen():
            yield f"data: {json.dumps({'type': 'text', 'content': '感谢使用外贸通，再见！👋'}, ensure_ascii=False)}\n\n"
            yield "data: {\"type\":\"done\"}\n\n"
        return Response(quit_gen(), mimetype="text/event-stream")

    if user_input.lower() in ['help', 'h', '帮助']:
        help_text = """## 📖 使用帮助

我可以帮您完成以下任务：

1. **🔍 买家搜索** - 根据关键词搜索潜在买家
   - 示例："帮我搜索电子产品相关的买家"

2. **📊 公司分析** - 分析指定公司的背景信息
   - 示例："分析一下 techglobal.com 这家公司"

3. **✉️ 开发信撰写** - 根据客户信息生成开发信
   - 示例："给 TechGlobal 写一封开发信，推销蓝牙耳机"

4. **💱 汇率查询** - 查询货币汇率
   - 示例："美元兑人民币的汇率是多少？"

5. **📝 商品描述生成** - 生成商品标题、卖点和描述
   - 示例："帮我为便携式加湿器生成商品描述"

6. **💬 客户回复起草** - 根据客户消息生成回复
   - 示例："客户问快递到哪了，帮我起草回复"

7. **📈 销售日报分析** - 分析销售数据生成日报
   - 示例："分析今天的销售数据：保温杯20个，手机支架35个"

8. **🎯 营销广告语生成** - 根据主题生成广告语
   - 示例："为夏日防晒衣生成几条广告语"

请直接输入您的需求，我会尽力帮助您！"""
        def help_gen():
            yield f"data: {json.dumps({'type': 'text', 'content': help_text}, ensure_ascii=False)}\n\n"
            yield "data: {\"type\":\"done\"}\n\n"
        return Response(help_gen(), mimetype="text/event-stream")

    if user_input.lower() in ['clear', '清空', '新会话']:
        if session_id in chat_history:
            del chat_history[session_id]
        def clear_gen():
            yield f"data: {json.dumps({'type': 'text', 'content': '会话已清空，我们可以开始新的对话了！'}, ensure_ascii=False)}\n\n"
            yield "data: {\"type\":\"done\"}\n\n"
        return Response(clear_gen(), mimetype="text/event-stream")

    needs_tools = _needs_tools(user_input)

    def generate():
        for event in run_agent_stream(user_input, session_id, use_tools=needs_tools, user_email=user_email):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "data: {\"type\":\"done\"}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route('/api/clear', methods=['POST'])
def clear_chat():
    """清空会话"""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    if session_id in chat_history:
        del chat_history[session_id]
    return jsonify({"success": True})


if __name__ == '__main__':
    print("=" * 60)
    print("[TradeMaster] Foreign Trade Assistant Web Service Starting...")
    print("=" * 60)
    print(f"URL: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)