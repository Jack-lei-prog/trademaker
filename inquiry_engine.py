# -*- coding: utf-8 -*-
"""
询盘自动回复引擎 — 闭环A
接收客户询盘 → 背景抓取 → 意图分类 → 个性化回复 → 加入跟进队列
"""
import json
import re
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from data_sources import (
    search_companies_opencorp,
    search_companies_wikidata,
    call_llm,
)

# ============================================================
# 1. 客户信息提取
# ============================================================

def extract_client_info(inquiry_text: str) -> dict:
    """
    从询盘文本中自动提取公司名称、邮箱、国家、产品兴趣等
    """
    result = {
        "company_name": "",
        "email": "",
        "country": "",
        "product_interest": "",
        "person_name": "",
        "phone": "",
        "website": "",
        "confidence": 0.0,
    }

    # 提取邮箱
    email_match = re.search(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}', inquiry_text)
    if email_match:
        result["email"] = email_match.group(0).lower()
        # 从邮箱域名提取公司名和网站
        domain = result["email"].split("@")[1]
        result["website"] = domain
        company_hint = domain.rsplit(".", 1)[0]
        if len(company_hint) > 2 and company_hint not in ("gmail", "yahoo", "hotmail", "outlook", "mail", "qq", "163", "126", "foxmail", "sina", "sohu"):
            result["company_name"] = company_hint.replace("-", " ").replace(".", " ").title()

    # 提取国家（中英文常见国家名）
    country_map = {
        "美国": "US", "usa": "US", "united states": "US",
        "英国": "UK", "uk": "UK", "united kingdom": "UK",
        "德国": "Germany", "germany": "Germany",
        "法国": "France", "france": "France",
        "日本": "Japan", "japan": "Japan",
        "韩国": "Korea", "korea": "Korea", "south korea": "Korea",
        "加拿大": "Canada", "canada": "Canada",
        "澳大利亚": "Australia", "australia": "Australia",
        "巴西": "Brazil", "brazil": "Brazil",
        "印度": "India", "india": "India",
        "俄罗斯": "Russia", "russia": "Russia",
        "墨西哥": "Mexico", "mexico": "Mexico",
        "意大利": "Italy", "italy": "Italy",
        "西班牙": "Spain", "spain": "Spain",
        "荷兰": "Netherlands", "netherlands": "Netherlands",
        "阿联酋": "UAE", "uae": "UAE", "dubai": "UAE",
        "沙特": "Saudi Arabia", "saudi": "Saudi Arabia",
        "土耳其": "Turkey", "turkey": "Turkey",
        "越南": "Vietnam", "vietnam": "Vietnam",
        "泰国": "Thailand", "thailand": "Thailand",
        "印尼": "Indonesia", "indonesia": "Indonesia",
        "马来西亚": "Malaysia", "malaysia": "Malaysia",
        "新加坡": "Singapore", "singapore": "Singapore",
        "南非": "South Africa", "south africa": "South Africa",
        "尼日利亚": "Nigeria", "nigeria": "Nigeria",
        "埃及": "Egypt", "egypt": "Egypt",
        "波兰": "Poland", "poland": "Poland",
    }
    lower = inquiry_text.lower()
    for name, code in country_map.items():
        if name.lower() in lower:
            result["country"] = code
            break

    # 提取人名（Mr./Ms. 或大写开头的英文名）
    name_match = re.search(r'(?:Mr\.?|Ms\.?|Dear|Attn:?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', inquiry_text)
    if name_match:
        result["person_name"] = name_match.group(1)

    # 提取产品关键词
    product_patterns = [
        r'(?:interested in|looking for|searching for|need|want to buy|want to purchase|采购|求购|需要|寻找)\s+(.{5,40}?)(?:\.|,|and|，|。|$)',
        r'(?:about|regarding|产品|about your)\s+(.{5,40}?)(?:\.|,|，|。|$)',
    ]
    for pat in product_patterns:
        m = re.search(pat, inquiry_text, re.IGNORECASE)
        if m:
            result["product_interest"] = m.group(1).strip().rstrip(".,;，。；")
            break

    # 提取电话
    phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}', inquiry_text)
    if phone_match:
        result["phone"] = phone_match.group(0)

    # 设置信度
    score = 0
    if result["email"]: score += 3
    if result["company_name"]: score += 2
    if result["country"]: score += 2
    if result["product_interest"]: score += 2
    if result["person_name"]: score += 1
    result["confidence"] = min(1.0, score / 8.0)

    return result


# ============================================================
# 2. 意图分类
# ============================================================

INQUIRY_TYPES = {
    "genuine_purchase": {
        "label": "真实采购",
        "strategy": "提供详细报价、产品规格、最小起订量，引导下单",
        "urgency": "high",
    },
    "price_shopping": {
        "label": "比价询价",
        "strategy": "强调差异化优势（质量/认证/售后），不急于报价，先建立信任",
        "urgency": "medium",
    },
    "market_research": {
        "label": "市场调研",
        "strategy": "提供产品资料和行业分析，展示专业度，等待时机",
        "urgency": "low",
    },
    "spam": {
        "label": "垃圾询盘",
        "strategy": "简短礼貌回复，不投入过多精力",
        "urgency": "ignore",
    },
}


def classify_inquiry(inquiry_text: str) -> dict:
    """用 LLM 分类询盘意图"""
    system = (
        "You are an international trade inquiry classifier. "
        "Analyze the inquiry and classify into one of:\n"
        "- genuine_purchase: real buyer with specific needs, likely to order\n"
        "- price_shopping: comparing prices from multiple suppliers\n"
        "- market_research: competitor or researcher gathering info, no immediate buying intent\n"
        "- spam: irrelevant, scam, or mass-sent inquiry\n\n"
        "Return ONLY a JSON object: "
        '{"type": "genuine_purchase|price_shopping|market_research|spam", '
        '"confidence": 0.0-1.0, "reasoning": "one brief sentence in Chinese", '
        '"urgency_score": 1-10, "suggested_approach": "one sentence in Chinese"}'
    )

    user = f"Inquiry:\n{inquiry_text[:1500]}"
    result = call_llm(system, user, max_tokens=2000, timeout=25)

    if result:
        try:
            text = result.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines)
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass

    return _quick_classify(inquiry_text)


def _quick_classify(inquiry_text: str) -> dict:
    """降级关键词分类"""
    lower = inquiry_text.lower()
    has_product = bool(re.search(r'(product|model|specs|specifications|价格|报价|规格|样品|interested in|looking for|need|want|price|quotation|catalog|order)', lower, re.IGNORECASE))
    has_quantity = bool(re.search(r'(\d+\s*(pcs|pieces|units|个|台|件|套|tons|kg|ctns|cartons)|MOQ|最小起订|trial order)', lower, re.IGNORECASE))
    has_company = bool(re.search(r'(company|inc|ltd|corp|co\.|公司|集团|ltd\.|limited|distributor|importer)', lower, re.IGNORECASE))
    has_cert = bool(re.search(r'\b(CE|RoHS|FCC|UL|FDA|ISO|SGS)\b|认证|certif', lower, re.IGNORECASE))
    has_deadline = bool(re.search(r'(urgent|asap|deadline|尽快|急|马上|this month|this week)', lower, re.IGNORECASE))
    spam_words = bool(re.search(r'(lottery|winner|inherit|prince|ngo|\bviagra\b|\bseo\b|make money|赚钱)', lower, re.IGNORECASE))

    if spam_words:
        return {"type": "spam", "confidence": 0.85, "reasoning": "含垃圾邮件特征词",
                "urgency_score": 0, "suggested_approach": "简短回复或忽略"}

    if has_product and has_quantity and has_company:
        return {"type": "genuine_purchase", "confidence": 0.72, "reasoning": "含产品+数量+公司信息",
                "urgency_score": 8, "suggested_approach": "迅速提供详细报价和产品资料"}
    if has_product and has_quantity:
        return {"type": "genuine_purchase", "confidence": 0.58, "reasoning": "含产品和数量信息",
                "urgency_score": 6, "suggested_approach": "提供报价，询问更多需求细节"}
    if has_cert and (has_product or has_quantity):
        return {"type": "genuine_purchase", "confidence": 0.55, "reasoning": "询问认证+产品，有明确采购需求",
                "urgency_score": 5, "suggested_approach": "提供认证信息和报价"}
    if has_product or has_quantity:
        return {"type": "price_shopping", "confidence": 0.45, "reasoning": "仅含产品信息",
                "urgency_score": 4, "suggested_approach": "强调差异化优势，提供产品资料"}
    if has_company:
        return {"type": "market_research", "confidence": 0.3, "reasoning": "含公司信息但无具体采购需求",
                "urgency_score": 2, "suggested_approach": "提供公司和产品介绍，保持联系"}

    return {"type": "price_shopping", "confidence": 0.3, "reasoning": "无法确定意图",
            "urgency_score": 3, "suggested_approach": "礼貌回复，询问具体需求"}


# ============================================================
# 3. 客户背景抓取
# ============================================================

def fetch_client_background(client_info: dict) -> dict:
    """
    根据提取的客户信息，搜索公司背景
    """
    background = {
        "company_name": client_info.get("company_name", ""),
        "website": client_info.get("website", ""),
        "country": client_info.get("country", ""),
        "company_data": None,
        "ai_supplement": "",
    }

    domain = client_info.get("website", "")
    company_name = client_info.get("company_name", "")
    search_query = company_name or domain

    if search_query and len(search_query) > 1:
        # 搜索 OpenCorporates
        results = search_companies_opencorp(search_query, limit=3)
        if not results:
            results = search_companies_wikidata(search_query, limit=3)
        if results:
            background["company_data"] = results[0]

    # 用 LLM 补充公司背景
    if background["company_data"] or domain:
        info_str = json.dumps(background["company_data"] or {}, ensure_ascii=False)
        system = "You are a business research assistant. Provide 2-3 sentences about this company's business focus and position in global trade. Be factual and concise."
        user = f"Company: {company_name}\nDomain: {domain}\nData: {info_str}"
        bg = call_llm(system, user, max_tokens=1000, timeout=25)
        if bg:
            background["ai_supplement"] = bg.strip()
        else:
            background["ai_supplement"] = f"{company_name or domain} — 通过商务数据库匹配到的潜在客户，建议进一步调研该公司在{client_info.get('country', '目标市场')}的业务规模。"

    return background


# ============================================================
# 4. 个性化回复生成
# ============================================================

def generate_inquiry_reply(
    inquiry_text: str,
    client_info: dict,
    background: dict,
    intent: dict,
    user_product: str = "",
    user_company: str = "",
    user_email: str = "",
    user_phone: str = "",
    language: str = "english",
) -> str:
    """生成个性化询盘回复"""

    intent_type = intent.get("type", "price_shopping")
    strategy = INQUIRY_TYPES.get(intent_type, INQUIRY_TYPES["price_shopping"])

    system = (
        "You are a professional international trade sales representative. "
        "Write a personalized reply to a customer inquiry. Follow these rules:\n"
        "1. Start by thanking the customer and referencing their specific request\n"
        "2. Recommend the best matching product(s) with key selling points\n"
        "3. Include a clear next step (send quote, arrange sample, video call, etc.)\n"
        f"4. Tone: professional but friendly, suitable for {client_info.get('country', 'international')} business culture\n"
        "5. Write in English unless the inquiry is in Chinese\n"
        f"6. Strategy: {strategy['strategy']}\n"
        "7. Include email subject line at the top: Subject: ...\n"
        "8. Return the complete email text, ready to send"
    )

    lang_hint = "Write in English."
    if any('一' <= c <= '鿿' for c in inquiry_text[:200]):
        lang_hint = "客户用中文询盘，请用中文回复。"

    user = f"""Customer inquiry:
{inquiry_text[:1200]}

Client info:
- Name: {client_info.get('person_name', 'Unknown')}
- Company: {client_info.get('company_name', 'Unknown')}
- Country: {client_info.get('country', 'Unknown')}
- Product interest: {client_info.get('product_interest', 'General')}

Client background:
{background.get('ai_supplement', 'No additional background available')}

Inquiry intent: {intent_type} ({strategy['label']})
Strategy: {strategy['strategy']}

Our product: {user_product or 'General products'}
Our company: {user_company or 'Our company'}
Our email: {user_email or ''}
Our phone: {user_phone or ''}

{lang_hint}

Generate the complete reply email:"""

    result = call_llm(system, user, max_tokens=2000, timeout=25)
    if result:
        return result.strip()

    # 降级模板
    subject = f"Re: {client_info.get('product_interest', 'Your Inquiry')} - {user_product or 'Product Information'}"
    name = client_info.get('person_name') or 'Sir/Madam'
    company = client_info.get('company_name', 'your company')

    return f"""Subject: {subject}

Dear {name},

Thank you for your inquiry! We are pleased to learn that {company} is interested in our products.

We are a professional manufacturer with {user_product or 'extensive product range'}, offering competitive pricing and reliable quality. All our products meet international standards (CE, RoHS, FCC certified).

Please let me know your specific requirements (quantity, specifications, target price) so I can prepare a detailed quotation for you.

Looking forward to working with you!

Best regards,
{user_company or 'Sales Team'}
Email: {user_email or ''}
Phone: {user_phone or ''}"""


# ============================================================
# 5. 跟进队列
# ============================================================

DEFAULT_FOLLOWUP_DAYS = 3
DEFAULT_ALERT_HOURS = 48


def _load_followups() -> List[Dict]:
    import db
    return db.load_followups()


def _save_followups(data: List[Dict]):
    import db
    db.save_followups(data)


def add_to_followup_queue(
    user_email: str,
    client_email: str,
    client_name: str = "",
    subject: str = "",
    inquiry_text: str = "",
    intent_type: str = "",
    auto_followup_days: int = DEFAULT_FOLLOWUP_DAYS,
) -> str:
    """将询盘加入跟进队列，返回 ID"""
    now = datetime.now()
    fuid = f"inq_{user_email}_{client_email}_{now.strftime('%Y%m%d%H%M%S')}"

    followups = _load_followups()
    followups.append({
        "id": fuid,
        "user_email": user_email,
        "client_email": client_email,
        "client_name": client_name,
        "subject": subject,
        "inquiry_preview": inquiry_text[:200],
        "intent_type": intent_type,
        "status": "pending",
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "replied_at": "",
        "followup_due": (now + timedelta(days=auto_followup_days)).strftime("%Y-%m-%d %H:%M:%S"),
        "alert_at": (now + timedelta(hours=DEFAULT_ALERT_HOURS)).strftime("%Y-%m-%d %H:%M:%S"),
        "alert_fired": False,
        "notes": "",
    })
    _save_followups(followups)
    return fuid


def get_pending_inquiries(user_email: str) -> List[Dict]:
    """获取待回复的询盘"""
    followups = _load_followups()
    return [f for f in followups if f.get("user_email") == user_email and f.get("status") == "pending"]


def get_alerts(user_email: str) -> List[Dict]:
    """获取需要提醒的询盘（超过 48h 未回复）"""
    now = datetime.now()
    followups = _load_followups()
    alerts = []
    for f in followups:
        if f.get("user_email") == user_email and f.get("status") == "pending" and not f.get("alert_fired"):
            alert_at = f.get("alert_at", "")
            if alert_at and now >= datetime.strptime(alert_at, "%Y-%m-%d %H:%M:%S"):
                f["alert_fired"] = True
                alerts.append(f)
    if alerts:
        _save_followups(followups)
    return alerts


def mark_inquiry_replied(fuid: str):
    """标记询盘已回复"""
    followups = _load_followups()
    for f in followups:
        if f.get("id") == fuid:
            f["status"] = "replied"
            f["replied_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    _save_followups(followups)


# ============================================================
# 6. 主流程编排
# ============================================================

def process_inquiry_full(
    inquiry_text: str,
    user_email: str = "",
    user_product: str = "",
    user_company: str = "",
    user_phone: str = "",
) -> dict:
    """
    完整询盘处理流程：
    extract → classify → background research → reply generation → follow-up queue
    """
    # Step 1: 提取客户信息
    client_info = extract_client_info(inquiry_text)

    # Step 2: 意图分类
    intent = classify_inquiry(inquiry_text)

    # Step 3: 背景抓取
    background = fetch_client_background(client_info)

    # Step 4: 生成回复
    reply = generate_inquiry_reply(
        inquiry_text=inquiry_text,
        client_info=client_info,
        background=background,
        intent=intent,
        user_product=user_product,
        user_company=user_company,
        user_email=user_email,
        user_phone=user_phone,
    )

    # Step 5: 加入跟进队列
    fuid = ""
    if user_email and client_info.get("email") and intent.get("type") != "spam":
        auto_days = DEFAULT_FOLLOWUP_DAYS
        if intent.get("urgency_score", 5) >= 7:
            auto_days = 2
        fuid = add_to_followup_queue(
            user_email=user_email,
            client_email=client_info.get("email", ""),
            client_name=client_info.get("person_name", client_info.get("company_name", "")),
            subject=f"Re: {client_info.get('product_interest', 'Inquiry')}",
            inquiry_text=inquiry_text,
            intent_type=intent.get("type", ""),
            auto_followup_days=auto_days,
        )

    return {
        "client_info": client_info,
        "intent": intent,
        "background": background,
        "reply": reply,
        "followup_id": fuid,
        "followup_due_days": 2 if intent.get("urgency_score", 5) >= 7 else DEFAULT_FOLLOWUP_DAYS,
    }
