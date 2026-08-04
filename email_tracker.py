# -*- coding: utf-8 -*-
"""
邮件跟踪服务
- 打开追踪（1x1 像素）
- 意图分类（LLM）
- 后端切换（Local / Gmail）
"""
import os
import json
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

from email_providers.local import LocalEmailProvider
from email_providers.gmail import GmailEmailProvider


# ============================================================
# 单例
# ============================================================

_local = None
_gmail = None


def get_local_provider() -> LocalEmailProvider:
    global _local
    if _local is None:
        _local = LocalEmailProvider()
    return _local


def get_gmail_provider() -> GmailEmailProvider:
    global _gmail
    if _gmail is None:
        _gmail = GmailEmailProvider()
    return _gmail


def get_provider(user_email: str = "") -> LocalEmailProvider:
    """获取当前活动的邮件后端。
    如果用户配置了 Gmail 则使用 Gmail，否则回退到 Local。
    """
    gmail = get_gmail_provider()
    if gmail.is_configured() and user_email in gmail.tokens:
        return gmail
    return get_local_provider()


# ============================================================
# 追踪像素
# ============================================================

def _load_pixels() -> dict:
    import db
    pixels = db.kv_get("tracking_pixels")
    if pixels is not None:
        return pixels
    # 首次从 JSON 文件迁移
    if os.path.exists("tracking_pixels.json"):
        try:
            with open("tracking_pixels.json", "r", encoding="utf-8") as f:
                pixels = json.load(f)
            db.kv_set("tracking_pixels", pixels)
            return pixels
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_pixels(data: dict):
    import db
    db.kv_set("tracking_pixels", data)


def generate_tracking_pixel(email_data: dict) -> str:
    """为邮件生成唯一的追踪 ID，返回追踪像素 URL"""
    tracking_id = hashlib.sha256(
        f"{email_data.get('from','')}{email_data.get('to','')}{datetime.now().isoformat()}".encode()
    ).hexdigest()[:16]

    pixels = _load_pixels()
    pixels[tracking_id] = {
        "email_from": email_data.get("from", ""),
        "email_to": email_data.get("to", ""),
        "subject": email_data.get("subject", ""),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "opens": [],
    }
    _save_pixels(pixels)
    return tracking_id


def record_open(tracking_id: str, ip: str, ua: str) -> bool:
    """记录一次打开事件"""
    pixels = _load_pixels()
    if tracking_id not in pixels:
        return False

    pixels[tracking_id]["opens"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip": ip,
        "user_agent": ua[:200] if ua else "",
    })

    # 限制只保留最近 50 次打开记录
    if len(pixels[tracking_id]["opens"]) > 50:
        pixels[tracking_id]["opens"] = pixels[tracking_id]["opens"][-50:]

    _save_pixels(pixels)

    # 同时更新邮件记录
    return get_local_provider().mark_opened(tracking_id)


def get_pixel_stats(tracking_id: str) -> dict:
    """获取某个追踪 ID 的打开统计"""
    pixels = _load_pixels()
    pixel = pixels.get(tracking_id, {})
    opens = pixel.get("opens", [])
    return {
        "tracking_id": tracking_id,
        "total_opens": len(opens),
        "first_open": opens[0]["time"] if opens else "",
        "last_open": opens[-1]["time"] if opens else "",
        "recent_opens": opens[-5:] if opens else [],
    }


# 1x1 透明 GIF（最小像素追踪图）
TRACKING_GIF = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61,  # GIF89a
    0x01, 0x00, 0x01, 0x00,               # 1x1 pixel
    0x80, 0x00, 0x00,                      # no global color table
    0xFF, 0xFF, 0xFF,                      # white background
    0x00, 0x00, 0x00,                      # black foreground
    0x2C, 0x00, 0x00, 0x00, 0x00,        # image descriptor
    0x01, 0x00, 0x01, 0x00,               # 1x1
    0x00, 0x02, 0x02, 0x44, 0x01, 0x00,  # LZW encoded data
    0x3B                                    # GIF trailer
])


# ============================================================
# 意图分类
# ============================================================

INTENT_CATEGORIES = {
    "inquiry": "询价查询 — 客户主动问价、要catalog",
    "price_negotiation": "议价 — 客户砍价、要求折扣",
    "sample_request": "索样 — 客户要样品",
    "order_confirmed": "已下单 — 客户确认订单、发PO",
    "rejection": "拒绝 — 客户说不感兴趣、已有供应商",
    "logistics": "物流询问 — 问发货时间、快递单号",
    "after_sales": "售后 — 投诉质量问题、退换货",
    "other": "其他咨询",
}


def classify_intent(reply_text: str, original_subject: str = "") -> dict:
    """用 LLM 分类客户回复意图"""
    from data_sources import call_llm

    system = (
        "You are an email intent classifier for international trade. "
        "Classify the customer's reply into one of these categories:\n"
        "- inquiry: asking for price, catalog, product details\n"
        "- price_negotiation: bargaining, asking for discount\n"
        "- sample_request: requesting samples\n"
        "- order_confirmed: confirmed order, sent PO\n"
        "- rejection: not interested, already have supplier\n"
        "- logistics: asking about shipping, tracking number\n"
        "- after_sales: complaint, quality issue, return/refund\n"
        "- other: anything else\n\n"
        "Return ONLY a JSON object: {\"intent\": \"...\", \"confidence\": 0.0-1.0, \"brief\": \"one-line summary in Chinese\"}"
    )

    user = f"Original subject: {original_subject}\n\nCustomer reply:\n{reply_text}"
    result = call_llm(system, user, max_tokens=200, timeout=10)

    if result:
        try:
            text = result.strip()
            # clean markdown fences
            if text.startswith("```"):
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines)
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass

    # 降级：简单关键词匹配
    lower = reply_text.lower()
    intent = "other"
    confidence = 0.3

    if any(w in lower for w in ["price", "quote", "cost", "discount", "cheaper", "报价", "价格", "便宜"]):
        intent = "inquiry"
        confidence = 0.5
    elif any(w in lower for w in ["order", "po", "purchase", "confirm", "下单", "订购", "确认"]):
        intent = "order_confirmed"
        confidence = 0.5
    elif any(w in lower for w in ["sample", "样品", "样板"]):
        intent = "sample_request"
        confidence = 0.5
    elif any(w in lower for w in ["not interested", "already have", "no thanks", "不要", "不考虑", "不需要"]):
        intent = "rejection"
        confidence = 0.5
    elif any(w in lower for w in ["tracking", "delivery", "ship", "快递", "物流", "发货"]):
        intent = "logistics"
        confidence = 0.5
    elif any(w in lower for w in ["broken", "damage", "return", "refund", "complaint", "退货", "退款", "投诉", "坏了"]):
        intent = "after_sales"
        confidence = 0.5

    return {"intent": intent, "confidence": confidence, "brief": ""}


def classify_and_update(user_email: str, to_email: str, reply_text: str,
                        subject: str = "") -> dict:
    """分类意图并自动更新邮件状态"""
    intent_result = classify_intent(reply_text, subject)

    provider = get_provider(user_email)
    # 更新状态为 replied，并存储意图
    provider.update_status(user_email, to_email, "replied")

    # 如果是已下单/拒绝，更新到更具体的状态
    if intent_result.get("intent") == "order_confirmed":
        provider.update_status(user_email, to_email, "replied_order")
    elif intent_result.get("intent") == "rejection":
        provider.update_status(user_email, to_email, "replied_rejected")

    return intent_result
