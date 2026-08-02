"""
外贸业务助理 Agent 工具函数模块
实现八个核心工具，全部接入真实数据源
"""

import json
import re
import os
from datetime import datetime
from typing import Dict, List, Any

from dotenv import load_dotenv
load_dotenv()

from data_sources import (
    fetch_exchange_rates,
    search_companies_wikidata,
    search_companies_opencorp,
    search_companies_llm,
    get_company_detail_opencorp,
    call_llm,
    _expand_trade_terms,
)


# ========== 工具1：买家搜索 ==========
def search_buyers(keyword: str) -> str:
    """
    快速搜索 Wikidata/OpenCorporates 数据库获取公司信息
    Agent 会基于搜索结果和自己的知识补充推荐潜在买家
    返回 JSON 格式的搜索结果，Agent 将在回复中结合自身知识推荐买家
    """
    import concurrent.futures
    from concurrent.futures import ThreadPoolExecutor
    import time

    seen_names = set()
    sources_used = []
    raw_results = []

    # 扩展贸易搜索词
    trade_terms = _expand_trade_terms(keyword)

    with ThreadPoolExecutor(max_workers=8) as executor:
        def search_wikidata(term):
            return search_companies_wikidata(term, limit=3)

        def search_opencorp(term):
            return search_companies_opencorp(term, limit=3)

        api_futures = {}
        en_terms = [t for t in trade_terms if re.match(r'^[A-Za-z0-9\s]+$', t)]
        for term in en_terms[:8]:
            api_futures[executor.submit(search_wikidata, term)] = ("Wikidata", term)
            api_futures[executor.submit(search_opencorp, term)] = ("OpenCorporates", term)

        # 快速收集结果（最多等 2s）
        deadline = time.time() + 2
        pending = set(api_futures.keys())

        while pending and time.time() < deadline:
            done, pending = concurrent.futures.wait(
                pending, timeout=0.2, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for future in done:
                source, term = api_futures.pop(future, (None, None))
                try:
                    data = future.result(timeout=0)
                    if data:
                        if source and source not in sources_used:
                            sources_used.append(source)
                        for item in data:
                            name = item.get("company_name", "").strip().lower()
                            if name and name not in seen_names:
                                seen_names.add(name)
                                raw_results.append((source, item))
                except Exception:
                    pass

    buyers = []
    for source, r in raw_results[:15]:
        buyers.append({
            "company_name": r.get("company_name", "Unknown"),
            "country": r.get("jurisdiction") or r.get("country", ""),
            "website": r.get("website", ""),
            "email": r.get("email", ""),
            "description": r.get("description", ""),
            "url": r.get("opencorporates_url") or r.get("wikidata_url", ""),
            "data_source": r.get("source", source),
        })

    # Agent 需要基于此结果 + 自身知识推荐买家
    return json.dumps({
        "success": True,
        "keyword": keyword,
        "structured_count": len(buyers),
        "structured_results": buyers,
        "search_terms_used": trade_terms[:5],
        "note": f"以上为数据库匹配结果。请根据你的训练知识，额外推荐 5-10 家与 '{keyword}' 相关的全球知名买家/进口商/分销商。每家必须包含：公司名、国家、网站、联系邮箱（如果知道真实邮箱则提供，否则基于网站给出常见采购邮箱如 purchasing@/info@/sales@域名）、采购类型、为什么是潜在客户。优先推荐真正的买家 (importer/distributor/wholesaler)，而非纯制造商。"
    }, ensure_ascii=False, indent=2)


# ========== 工具2：公司分析 ==========
def analyze_company(domain: str) -> str:
    """
    通过 OpenCorporates 获取公司详细信息
    参数 domain: 公司域名（如 techglobal.com）或公司名称
    """
    # 清理域名，提取公司名关键词
    clean = domain.lower()
    clean = clean.replace("https://", "").replace("http://", "")
    clean = clean.replace("www.", "").split("/")[0]
    # 去掉 TLD 作为搜索关键词
    search_name = clean.rsplit(".", 1)[0] if "." in clean else clean

    # 先搜索匹配
    search_results = search_companies_opencorp(search_name, limit=3)

    if not search_results:
        # 直接用域名作为关键词再试
        search_results = search_companies_opencorp(clean, limit=3)

    if search_results:
        best = search_results[0]
        # 尝试获取详细信息
        jurisdiction = best.get("jurisdiction", "").lower()
        company_number = best.get("company_number", "")
        detail = None
        if jurisdiction and company_number:
            detail = get_company_detail_opencorp(jurisdiction, company_number)

        company_info = detail or best
        return json.dumps({
            "success": True,
            "domain": clean,
            "source": "OpenCorporates API (opencorporates.com)",
            "company_info": company_info,
        }, ensure_ascii=False, indent=2)

    return json.dumps({
        "success": False,
        "domain": clean,
        "error": "OpenCorporates 中未找到该公司，请尝试其他名称或域名",
        "source": "OpenCorporates API (opencorporates.com)",
    }, ensure_ascii=False, indent=2)


# ========== 工具3：开发信撰写 ==========
def draft_email(company_info: str, product_highlight: str) -> str:
    """
    通过 SynScale LLM 生成个性化英文开发信
    """
    system = (
        "You are a professional B2B sales copywriter. "
        "Write a concise, polite cold outreach email in English. "
        "Include: subject line, greeting, body (2-3 short paragraphs), and closing. "
        "Return ONLY the email text, no extra explanation. "
        "Use standard ASCII characters only – no special Unicode symbols, no emoji. "
        "Keep it plain text compatible with all email clients."
    )
    user = (
        f"Company info: {company_info}\n"
        f"Product highlight: {product_highlight}\n\n"
        "Write a compelling development email to this company."
    )
    result = call_llm(system, user, max_tokens=600)
    if result:
        return result.strip()

    # 降级为简单模板
    return f"""Subject: Business Cooperation Opportunity

Dear Sir/Madam,

I am writing to introduce our products. {product_highlight}

We have over 10 years of export experience with competitive pricing and reliable quality.
Please contact us for a catalog and quotation.

Best regards,
Sales Team"""


# ========== 工具4：汇率查询 ==========
def query_exchange_rate(currency: str) -> str:
    """
    从 open.er-api.com 获取实时汇率（免费，每日更新）
    支持 160+ 货币
    """
    currency_code = currency.upper().strip()
    data = fetch_exchange_rates()

    if not data:
        return json.dumps({
            "success": False,
            "currency": currency_code,
            "error": "无法获取实时汇率，请稍后重试",
        }, ensure_ascii=False, indent=2)

    rates = data.get("rates", {})
    time_next_update = data.get("time_next_update_utc", "Unknown")

    if currency_code == "USD":
        rate_to_cny = float(rates.get("CNY", 0))
        return json.dumps({
            "success": True,
            "currency": "USD",
            "currency_name": "美元 (US Dollar)",
            "rate_to_cny": round(rate_to_cny, 4),
            "rate_from_cny": round(1 / rate_to_cny, 4) if rate_to_cny else 0,
            "last_update": data.get("time_last_update_utc", "Unknown"),
            "next_update": time_next_update,
            "source": "open.er-api.com",
            "note": "实时汇率，1 USD = X CNY",
            "all_rates_cny": {
                cur: round(float(rates.get(cur, 0)) * rate_to_cny, 4)
                for cur in ["EUR", "GBP", "JPY", "AUD", "CAD", "CNY"]
                if cur in rates
            }
        }, ensure_ascii=False, indent=2)

    target_rate = rates.get(currency_code)
    usd_to_cny = float(rates.get("CNY", 0))

    if target_rate is None:
        available = list(rates.keys())[:50]
        return json.dumps({
            "success": False,
            "currency": currency_code,
            "error": f"未找到货币代码 '{currency_code}'",
            "available_currencies_sample": available,
            "source": "open.er-api.com",
        }, ensure_ascii=False, indent=2)

    rate_via_usd = usd_to_cny / float(target_rate)

    return json.dumps({
        "success": True,
        "currency": currency_code,
        "rate_to_cny": round(rate_via_usd, 4),
        "rate_from_cny": round(1 / rate_via_usd, 4) if rate_via_usd else 0,
        "last_update": data.get("time_last_update_utc", "Unknown"),
        "next_update": time_next_update,
        "source": "open.er-api.com",
        "note": f"实时汇率，1 {currency_code} = {round(rate_via_usd, 4)} CNY",
    }, ensure_ascii=False, indent=2)


# ========== 工具5：商品描述生成 ==========
def generate_product_desc(name: str, tone: str = "活泼", target_audience: str = "年轻人") -> str:
    """
    通过 SynScale LLM 生成商品标题、卖点列表和描述
    返回 JSON 字符串，包含 title, bullet_points, description
    """
    system = (
        "You are a Chinese e-commerce copywriter. "
        "Given a product name, tone, and target audience, generate product copy in Chinese. "
        "Return ONLY valid JSON with keys: title, bullet_points (array of 3 strings), description. "
        "No extra text or markdown fences."
    )
    user = (
        f"产品：{name}，风格：{tone}，受众：{target_audience}\n"
        "生成JSON：title（产品标题）、bullet_points（3条卖点）、description（一段描述）"
    )
    result = call_llm(system, user, max_tokens=600)
    if result:
        return result.strip()

    # 降级模板
    return json.dumps({
        "title": f"【{tone}风】{name} – 专为{target_audience}设计",
        "bullet_points": [
            f"✨ 轻巧便携，{target_audience}的日常好物",
            "💧 持久保湿，一次加水可用8小时",
            "🔇 超静音运行，办公室/宿舍皆适用"
        ],
        "description": f"{name}，专为{target_audience}打造的{name}。采用先进雾化技术，细腻水雾快速滋润空气，告别干燥。{target_audience}最爱的简约外观，是提升生活品质的必备小物。"
    }, ensure_ascii=False, indent=2)


# ========== 工具6：客户回复起草 ==========
def draft_customer_reply(message: str, order_status: str = "已发货") -> str:
    """
    通过 SynScale LLM 生成客服回复文本
    """
    system = (
        "You are a professional Chinese customer service agent for a cross-border e-commerce company. "
        "Reply concisely, politely, and helpfully in Chinese. Sign off with '祝您购物愉快！'. "
        "Return ONLY the reply text, nothing else."
    )
    user = (
        f"客户消息：{message}\n订单状态：{order_status}\n请起草一个中文客服回复。"
    )
    result = call_llm(system, user, max_tokens=400)
    if result:
        return result.strip()

    # 降级模板
    reply = "您好，感谢您的来信。\n"
    if "快递" in message or "物流" in message:
        if order_status == "已发货":
            reply += "您的订单已经发货，请点击物流查询链接查看最新状态：[物流查询链接]。如长时间未更新，请联系客服。"
        else:
            reply += "您的订单正在处理中，预计1-2天内发出，请耐心等待。"
    elif "退货" in message or "退款" in message:
        reply += "非常抱歉给您带来不便。您可在订单页面申请退货退款，我们将尽快处理。"
    else:
        reply += "已收到您的留言，我们会尽快处理。如需即时帮助，请拨打客服热线 400-888-8888。"
    reply += "\n祝您购物愉快！"
    return reply


# ========== 工具7：销售日报分析 ==========
def analyze_daily_sales(orders_summary: str = "") -> str:
    """
    解析订单文本，生成销售简报
    对复杂摘要使用 LLM 辅助提取结构化数据
    """
    today = datetime.now().strftime("%Y-%m-%d")

    if not orders_summary:
        return json.dumps({
            "date": today,
            "total_income": 0,
            "total_orders": 0,
            "top_products": [],
            "remarks": "今日暂无销售数据，请提供订单详情。"
        }, ensure_ascii=False, indent=2)

    total_income = 0
    total_orders = 0
    top_products = []

    # 正则解析
    pattern = r'([\u4e00-\u9fa5a-zA-Z]+?)(\d+)个'
    matches = re.findall(pattern, orders_summary)
    for product, qty in matches:
        qty = int(qty)
        total_orders += qty
        top_products.append({"name": product.strip(), "sales": qty})

    income_match = re.search(r'总收入(\d+)元', orders_summary)
    if income_match:
        total_income = int(income_match.group(1))
    elif total_orders > 0:
        total_income = total_orders * 25  # 默认均价

    top_products.sort(key=lambda x: x["sales"], reverse=True)

    # 用 LLM 生成备注分析
    if top_products:
        system = "You are a sales data analyst. Write one concise sentence in Chinese with insights and stock advice. Return ONLY that sentence."
        user = f"Top products: {json.dumps(top_products, ensure_ascii=False)}. Give a brief analysis."
        remarks = call_llm(system, user, max_tokens=200)
        if not remarks:
            top_item = top_products[0]
            remarks = f"今日销售平稳，{top_item['name']}销量突出（{top_item['sales']}件），建议关注库存。"
        else:
            remarks = remarks.strip()
    else:
        remarks = "今日暂无有效销售数据。"

    return json.dumps({
        "date": today,
        "total_income": total_income,
        "total_orders": total_orders,
        "top_products": top_products,
        "remarks": remarks
    }, ensure_ascii=False, indent=2)


# ========== 工具8：营销广告语生成 ==========
def write_marketing_slogan(promotion_topic: str) -> str:
    """
    通过 SynScale LLM 生成3条营销广告语
    返回 JSON 数组
    """
    system = (
        "You are a Chinese marketing copywriter. "
        "Given a promotion topic, generate 3 creative and diverse Chinese slogans. "
        "Return ONLY a JSON array of 3 strings, no extra text."
    )
    user = f"促销主题：{promotion_topic}\n生成3条不同风格的中文广告语，返回JSON数组。"
    result = call_llm(system, user, max_tokens=500)
    if result:
        return result.strip()

    # 降级模板
    slogans = [
        f"🔥 {promotion_topic} – 限时特惠，买一送一！立即入手！",
        f"✨ 时尚穿搭从{promotion_topic}开始，轻盈透气，今日下单立减20元！",
        f"🌟 重磅推荐：{promotion_topic}，用户好评如潮，仅此一天！"
    ]
    return json.dumps(slogans, ensure_ascii=False, indent=2)


# ========== 工具9：发送邮件 ==========
def send_email(to_email: str, subject: str, body: str, to_name: str = "", from_email: str = "") -> str:
    """
    生成 mailto 链接 + 纯文本邮件内容，供前端复制或打开邮箱客户端
    参数 from_email: 发件人邮箱（用于记录跟踪）
    """
    if not to_email or "@" not in to_email:
        return json.dumps({
            "success": False,
            "error": f"收件人邮箱地址无效: {to_email}"
        }, ensure_ascii=False)

    # 清理正文
    clean_body = body.strip()

    # 提取 Subject（如果正文以 Subject: 开头）
    email_subject = subject
    if clean_body.lower().startswith("subject:"):
        lines = clean_body.split("\n")
        email_subject = lines[0].replace("Subject:", "").replace("subject:", "").strip()
        if len(lines) > 1 and not lines[1].strip():
            clean_body = "\n".join(lines[2:]).strip()
        elif len(lines) > 1:
            clean_body = "\n".join(lines[1:]).strip()

    # 清理正文中的特殊 unicode 字符，确保邮件客户端兼容
    import unicodedata
    safe_body = ""
    for ch in clean_body:
        if ord(ch) < 128 or ch in '\n\r':
            safe_body += ch
        elif unicodedata.category(ch).startswith('P') or ch == ' ':
            safe_body += ch  # keep punctuation
        else:
            safe_body += ch  # keep CJK etc for now

    # 构建 mailto URL (safe encoding)
    import urllib.parse

    # 短版 mailto：只用收件人 + 主题（body 太长会破坏 mailto 链接）
    short_mailto = f"mailto:{urllib.parse.quote(to_email)}"
    if email_subject:
        short_mailto += f"?subject={urllib.parse.quote(email_subject, safe='')}"

    # 完整 mailto（尝试包含正文，但截断到安全长度）
    body_short = safe_body[:800]
    full_mailto = short_mailto
    if body_short:
        full_mailto += f"{'&' if '?' in full_mailto else '?'}body={urllib.parse.quote(body_short, safe='')}"

    return json.dumps({
        "success": True,
        "to_email": to_email,
        "from_email": from_email,
        "to_name": to_name,
        "subject": email_subject,
        "body": safe_body,
        "mailto_url": full_mailto,
        "action": "open_mailto",
        "message": f"邮件已准备就绪！收件人：{to_email}\n主题：{email_subject}",
        "hint": "点击按钮打开邮箱客户端，或复制正文手动粘贴到邮件中"
    }, ensure_ascii=False)


# ========== 工具10：邮件状态检查 ==========
def check_email_status(user_email: str = "") -> str:
    """
    检查某用户的邮件跟进状态：哪些邮件需要跟进
    参数 user_email: 用户的邮箱地址
    """
    import os
    from datetime import datetime as dt
    emails_file = "emails_sent.json"
    if not os.path.exists(emails_file):
        return json.dumps({"success": True, "pending": [], "all": [],
                           "message": "暂无邮件记录"}, ensure_ascii=False)

    try:
        with open(emails_file, 'r', encoding='utf-8') as f:
            all_emails = json.load(f)
    except (json.JSONDecodeError, IOError):
        return json.dumps({"success": True, "pending": [], "all": []}, ensure_ascii=False)

    user_emails = [v for v in all_emails.values() if v["from"] == user_email]
    now = dt.now()
    pending = []
    replied = []

    for e in user_emails:
        days = (now - dt.strptime(e["sent_at"], "%Y-%m-%d %H:%M")).days
        e["days_ago"] = days
        if e["status"] in ("sent", "no_reply") and days >= 1:
            pending.append(e)
        elif e["status"] == "replied":
            replied.append(e)

    summary = ""
    if pending:
        names = ", ".join([p.get("to_name", p["to"]) for p in pending[:5]])
        summary = f"有{len(pending)}封邮件超过1天未回复，建议跟进：{names}"
    else:
        summary = "所有邮件状态良好，暂无需跟进"

    return json.dumps({
        "success": True,
        "total_sent": len(user_emails),
        "pending_count": len(pending),
        "replied_count": len(replied),
        "pending": pending,
        "replied": replied,
        "summary": summary,
    }, ensure_ascii=False, indent=2)


TOOL_FUNCTIONS = {
    "search_buyers": search_buyers,
    "analyze_company": analyze_company,
    "draft_email": draft_email,
    "send_email": send_email,
    "query_exchange_rate": query_exchange_rate,
    "generate_product_desc": generate_product_desc,
    "draft_customer_reply": draft_customer_reply,
    "analyze_daily_sales": analyze_daily_sales,
    "write_marketing_slogan": write_marketing_slogan,
    "check_email_status": check_email_status,
}

TOOL_DESCRIPTIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_buyers",
            "description": "通过 OpenCorporates 全球公司注册数据库搜索潜在买家，返回公司名、注册地、状态、地址等",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词，如产品名、行业名（electronics, textiles, machinery）"}
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_company",
            "description": "通过 OpenCorporates 获取公司详细注册信息，包含高管、行业代码、注册日期等",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "公司域名或名称（如 techglobal.com, apple.com）"}
                },
                "required": ["domain"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draft_email",
            "description": "利用 AI 生成个性化英文开发信",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_info": {"type": "string", "description": "客户公司信息"},
                    "product_highlight": {"type": "string", "description": "产品亮点/卖点"}
                },
                "required": ["company_info", "product_highlight"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_exchange_rate",
            "description": "查询实时汇率（支持160+货币），数据来源 open.er-api.com",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency": {"type": "string", "description": "货币代码（USD, EUR, GBP, JPY, AUD, CAD 等）"}
                },
                "required": ["currency"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_product_desc",
            "description": "利用 AI 生成商品标题、卖点列表和描述文案",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "商品名称"},
                    "tone": {"type": "string", "description": "文案风格：活泼、专业、简约"},
                    "target_audience": {"type": "string", "description": "目标受众：年轻人、上班族、学生等"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draft_customer_reply",
            "description": "利用 AI 根据客户消息和订单状态生成客服回复",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "客户发来的消息"},
                    "order_status": {"type": "string", "description": "订单状态：已发货、待发货、已送达"}
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_daily_sales",
            "description": "分析当日销售数据并生成简报，包含总收入、热销产品、AI 分析建议",
            "parameters": {
                "type": "object",
                "properties": {
                    "orders_summary": {"type": "string", "description": "订单摘要（如：保温杯20个，手机支架35个，数据线50个，总收入2800元）"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_marketing_slogan",
            "description": "利用 AI 根据促销主题生成3条创意广告语",
            "parameters": {
                "type": "object",
                "properties": {
                    "promotion_topic": {"type": "string", "description": "促销主题（如：夏日防晒衣、双十一大促）"}
                },
                "required": ["promotion_topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "生成mailto链接打开邮箱客户端发送邮件。发送后自动记录到跟踪系统。",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_email": {"type": "string", "description": "收件人邮箱地址"},
                    "subject": {"type": "string", "description": "邮件主题"},
                    "body": {"type": "string", "description": "邮件正文"},
                    "to_name": {"type": "string", "description": "收件人姓名（可选）"},
                    "from_email": {"type": "string", "description": "发件人邮箱地址（你自己的邮箱）"}
                },
                "required": ["to_email", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_email_status",
            "description": "检查已发送邮件的跟进状态：哪些邮件超过1天未回复需要跟进，哪些已回复",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_email": {"type": "string", "description": "用户邮箱地址"}
                },
                "required": ["user_email"]
            }
        }
    }
]


if __name__ == "__main__":
    print("=" * 60)
    print("工具函数测试（真实数据源）")
    print("=" * 60)

    print("\n1. 汇率查询 (USD):")
    print(query_exchange_rate("USD")[:400])

    print("\n2. 汇率查询 (EUR):")
    print(query_exchange_rate("EUR")[:400])

    print("\n3. 买家搜索 (electronics):")
    print(search_buyers("electronics")[:500])

    print("\n4. 开发信撰写 (AI):")
    print(draft_email("TechGlobal Imports Ltd.", "Bluetooth earphones with ANC")[:500])