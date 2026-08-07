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
    enrich_result,
    DATA_SOURCE_STATUS,
)
from cache import cached


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

        # 如果 API 没返回结果，用 LLM 补充
        if not raw_results:
            llm_companies = search_companies_llm(keyword, limit=10)
            for c in llm_companies:
                name = c.get("company_name", "").strip().lower()
                if name and name not in seen_names:
                    seen_names.add(name)
                    raw_results.append(("AI Trade DB", c))
            if not sources_used:
                sources_used.append("AI Trade Database")

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
    # 构建可操作的买家联系路径
    keyword_encoded = keyword.replace(" ", "%20")
    alibaba_rfq_url = f"https://www.alibaba.com/trade/search?spm=a2700.galleryofferlist.rfq_search&IndexArea=rfq_en&SearchText={keyword_encoded}"
    linkedin_url = f"https://www.linkedin.com/search/results/people/?keywords={keyword_encoded}%20buyer%20OR%20purchasing%20OR%20sourcing"
    google_url = f"https://www.google.com/search?q={keyword_encoded}+importer+OR+distributor+OR+wholesaler+email"

    # 数据源降级警告
    degraded_sources = [k for k, v in DATA_SOURCE_STATUS.items() if v != "ok"]
    degradation_warning = ""
    if degraded_sources:
        degradation_warning = (
            f"\n\n⚠️ 部分数据源暂时不可用: {', '.join(degraded_sources)}。"
            f"结果可能不完整，建议稍后重试或使用其他搜索词。"
        )

    base_note = (
        f"数据库匹配结果有限（结构化为{len(buyers)}条）。你必须提供可操作的替代联系路径，而非编造邮箱。\n\n"
        f"## 产品: {keyword}\n\n"
        f"### 可选路径（每条都给具体链接）\n"
        f"1. 🛒 Alibaba RFQ: {alibaba_rfq_url}\n"
        f"2. 💼 LinkedIn搜索: {linkedin_url}\n"
        f"3. 🔍 Google搜索: {google_url}\n"
        f"4. 📅 展会采购商名录 → 调用 search_trade_knowledge 工具查询相关展会\n\n"
        f"### 补充推荐（基于行业知识）\n"
        f"根据你的行业知识，推荐3-5家真实的全球买家/进口商/分销商：\n"
        f"- 每家提供：公司名（真实存在）+ 国家 + 网站 + 采购类型 + 为何相关\n"
        f"- 知名大企业 → 给供应商注册URL\n"
        f"- 中小公司 → 给出 LinkedIn 搜索链接（搜索\"公司名 procurement\"）\n"
        f"- 如果无法验证邮箱 → 明确说\"无公开邮箱，建议通过LinkedIn联系其采购经理\"\n"
        f"- 禁止编造邮箱！宁缺毋滥！\n\n"
        f"格式：序号. 公司名 🇺🇸 — site.com | 采购类型 | 联系途径（LinkedIn/Alibaba/展会/供应商门户）"
    ) + degradation_warning

    from datetime import timezone as _tz
    return json.dumps({
        "success": True,
        "keyword": keyword,
        "structured_count": len(buyers),
        "structured_results": buyers,
        "search_terms_used": trade_terms[:5],
        "note": base_note,
        "fetched_at": datetime.now(_tz.utc).isoformat(),
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
    result = call_llm(system, user, max_tokens=2000)
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
    result = call_llm(system, user, max_tokens=2000)
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
    result = call_llm(system, user, max_tokens=2000)
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
    pattern = r'([\u4e00-\u9fa5a-zA-Z0-9]+?)\s*(\d+)个'
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
        remarks = call_llm(system, user, max_tokens=1000)
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
    result = call_llm(system, user, max_tokens=2000)
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

    # 知名企业供应商门户域名检测
    enterprise_domains = {
        "ikea.com": "IKEA 通过供应商门户采购，不接收开发信 → https://supplier.ikea.com",
        "walmart.com": "Walmart 通过 Retail Link 管理供应商 → https://walmart.com/suppliers",
        "amazon.com": "Amazon 通过 Seller Central 入驻 → https://sell.amazon.com",
        "homedepot.com": "Home Depot 通过 Supplier Center 管理 → https://homedepot.com/suppliers",
        "target.com": "Target 通过 Partners Online 管理 → https://corporate.target.com/suppliers",
        "costco.com": "Costco 通过 Supplier Diversity 注册 → https://costco.com/supplier-diversity.html",
        "bestbuy.com": "Best Buy 通过 Partner Portal 管理 → https://bestbuy.com/suppliers",
        "tesco.com": "Tesco 通过 Supplier Network 管理 → https://tesco.com/suppliers",
        "carrefour.com": "Carrefour 通过供应商平台采购 → https://carrefour.com/suppliers",
    }
    domain = to_email.split("@")[1].lower()
    if domain in enterprise_domains:
        return json.dumps({
            "success": False,
            "error": f"发送已阻止。{enterprise_domains[domain]}",
            "hint": "大型企业通过供应商门户采购，开发信不会有效果。请通过上述链接注册成为其供应商。"
        }, ensure_ascii=False)

    # 推测邮箱检测
    guessed_patterns = ["purchasing@", "info@", "sales@", "inquiry@", "procurement@",
                       "import@", "export@", "contact@", "admin@", "office@"]

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

    # 检查是否为推测邮箱
    is_guessed = any(to_email.lower().startswith(p) for p in guessed_patterns)
    if is_guessed:
        clean_body = (
            f"[⚠️ 此邮箱为基于域名推测，未经验证，建议先用 Hunter.io 等工具验证]\n\n"
            f"{clean_body}"
        )

    # 邮件内容直接展示在页面内联编辑器中
    return json.dumps({
        "success": True,
        "to_email": to_email,
        "from_email": from_email,
        "to_name": to_name,
        "subject": email_subject,
        "body": clean_body,
        "action": "inline_composer",
        "message": "邮件已生成" if not is_guessed else "邮件已生成（⚠️ 推测邮箱，建议验证后发送）",
        "email_verified": not is_guessed,
        "hint": "在页面编辑器中直接编辑后，复制粘贴到你的邮箱客户端发送" if not is_guessed
                else "⚠️ 推测邮箱未验证，强烈建议用 Hunter.io / FindThatLead / Snov.io 验证后再发送，避免退信"
    }, ensure_ascii=False)


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


# ========== 工具11：询盘处理 ==========
def process_inquiry(inquiry_text: str, user_email: str = "",
                    user_product: str = "", user_company: str = "",
                    user_phone: str = "") -> str:
    """完整询盘处理：提取客户→分类意图→背景调研→生成回复→跟进队列"""
    from inquiry_engine import process_inquiry_full

    result = process_inquiry_full(
        inquiry_text=inquiry_text, user_email=user_email,
        user_product=user_product, user_company=user_company, user_phone=user_phone)

    intent_label = {"genuine_purchase": "真实采购", "price_shopping": "比价询价",
                    "market_research": "市场调研", "spam": "垃圾询盘"}

    summary = (
        f"Company: {result['client_info'].get('company_name', 'N/A')}\n"
        f"Email: {result['client_info'].get('email', 'N/A')}\n"
        f"Country: {result['client_info'].get('country', 'N/A')}\n"
        f"Intent: {intent_label.get(result['intent'].get('type', ''), 'Unknown')} "
        f"(confidence: {float(result['intent'].get('confidence', 0)):.0%})\n"
        f"Follow-up: {result.get('followup_due_days', 3)} days")

    return json.dumps({
        "success": True,
        "inquiry_analysis": {
            "client_info": result["client_info"],
            "intent": result["intent"],
            "background": result["background"],
            "summary": summary,
        },
        "reply_email": result["reply"],
        "followup_id": result.get("followup_id", ""),
        "followup_due_days": result.get("followup_due_days", 3),
    }, ensure_ascii=False, indent=2)


# ========== 工具12：知识库检索（RAG）==========
def search_trade_knowledge(query: str) -> str:
    """
    RAG检索 — 从展会/认证/外贸术语知识库中检索相关内容
    """
    from knowledge.retriever import search_knowledge, lookup_term
    # 如果是简短术语，直接查术语库
    if len(query.strip().split()) <= 3:
        term_result = lookup_term(query)
        if "未找到" not in term_result:
            return json.dumps({"success": True, "type": "术语解释", "result": term_result},
                            ensure_ascii=False, indent=2)

    result = search_knowledge(query, top_k=5)
    # 附加参展商搜索链接
    from knowledge.tradeshows import get_exhibitor_search_urls
    exhibitor_links = get_exhibitor_search_urls(query)

    return json.dumps({
        "success": True,
        "query": query,
        "type": "知识库RAG检索",
        "tradeshows": result["tradeshows"][:3],
        "certifications": result["certifications"][:3],
        "exhibitor_search": exhibitor_links,
        "note": "基于TF-IDF语义匹配的知识库检索结果。含展会参展商名录+Alibaba RFQ+LinkedIn搜索链接。"
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
    "process_inquiry": process_inquiry,
    "search_trade_knowledge": search_trade_knowledge,
}

TOOL_DESCRIPTIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_buyers",
            "description": "通过 OpenCorporates 全球公司注册数据库搜索潜在买家",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词"}
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_company",
            "description": "通过 OpenCorporates 获取公司详细注册信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "公司域名或名称"}
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
                    "product_highlight": {"type": "string", "description": "产品亮点"}
                },
                "required": ["company_info", "product_highlight"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_exchange_rate",
            "description": "查询实时汇率（支持160+货币）",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency": {"type": "string", "description": "货币代码"}
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
                    "tone": {"type": "string", "description": "文案风格"},
                    "target_audience": {"type": "string", "description": "目标受众"}
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
                    "message": {"type": "string", "description": "客户消息"},
                    "order_status": {"type": "string", "description": "订单状态"}
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_daily_sales",
            "description": "分析当日销售数据并生成简报",
            "parameters": {
                "type": "object",
                "properties": {
                    "orders_summary": {"type": "string", "description": "订单摘要"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_marketing_slogan",
            "description": "利用 AI 生成3条创意广告语",
            "parameters": {
                "type": "object",
                "properties": {
                    "promotion_topic": {"type": "string", "description": "促销主题"}
                },
                "required": ["promotion_topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "生成mailto链接打开邮箱客户端发送邮件",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_email": {"type": "string", "description": "收件人邮箱"},
                    "subject": {"type": "string", "description": "邮件主题"},
                    "body": {"type": "string", "description": "邮件正文"},
                    "to_name": {"type": "string", "description": "收件人姓名"},
                    "from_email": {"type": "string", "description": "发件人邮箱"}
                },
                "required": ["to_email", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_email_status",
            "description": "检查已发送邮件的跟进状态",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_email": {"type": "string", "description": "用户邮箱地址"}
                },
                "required": ["user_email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "process_inquiry",
            "description": "分析客户询盘：提取公司信息、分类意图、调研背景、生成回复、加入跟进队列",
            "parameters": {
                "type": "object",
                "properties": {
                    "inquiry_text": {"type": "string", "description": "客户询盘的完整文本"},
                    "user_email": {"type": "string", "description": "用户邮箱（用于跟进）"},
                    "user_product": {"type": "string", "description": "主营产品（可选）"},
                    "user_company": {"type": "string", "description": "公司名称（可选）"},
                    "user_phone": {"type": "string", "description": "电话（可选）"}
                },
                "required": ["inquiry_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_trade_knowledge",
            "description": "RAG知识库检索：搜索展会信息、出口认证要求、外贸术语解释（如FOB/CIF/MOQ/CE/FCC等）",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索查询（产品关键词或外贸术语）"}
                },
                "required": ["query"]
            }
        }
    }
]


if __name__ == "__main__":
    print("=" * 60)
    print("工具函数测试")
    print("=" * 60)
    print("1. 汇率查询 (USD):")
    print(query_exchange_rate("USD")[:400])
    print("2. 开发信撰写:")
    print(draft_email("TechGlobal Imports Ltd.", "Bluetooth earphones with ANC")[:400])