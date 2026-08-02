"""
GAN-Style Evaluator Module
Hybrid: instant heuristics scoring + optional DeepSeek deep evaluation.

Generator = TradeMaster Agent
Discriminator = Heuristics (fast) + DeepSeek (deep, on-demand)
"""

import json
import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

_eval_session = None


def _get_session():
    global _eval_session
    if _eval_session is None:
        _eval_session = requests.Session()
    return _eval_session


def heuristic_evaluate(question, answer):
    """
    Instant rule-based evaluation. No API call needed.
    Returns same format as deep_evaluate.
    """
    scores = {}
    strengths = []
    weaknesses = []

    q_lower = question.lower()

    # 1. Relevance: topic matching + structural clues
    # Extract meaningful keywords (2+ chars)
    cn_words = re.findall(r"[一-鿿]{2,}", question)
    en_words = re.findall(r"[a-zA-Z]{2,}", question)
    topic_keywords = cn_words + en_words
    relevant_count = sum(1 for kw in topic_keywords if kw.lower() in answer.lower())
    if topic_keywords:
        relevance = 4 + (relevant_count / len(topic_keywords)) * 6
    else:
        relevance = 7

    # Structural relevance: email question → email structure in answer
    if any(w in q_lower for w in ["开发信", "邮件", "email"]) and re.search(r"(?i)subject|dear|best regards", answer):
        relevance = max(relevance, 8)
    if any(w in q_lower for w in ["买家", "buyer", "搜索"]) and re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+", answer):
        relevance = max(relevance, 8)
    if any(w in q_lower for w in ["汇率", "exchange"]) and re.search(r"\d+\.\d+", answer):
        relevance = max(relevance, 8)
    scores["relevance"] = round(min(10, relevance), 1)

    # 2. Completeness: check for key elements based on question type
    if any(w in q_lower for w in ["开发信", "邮件", "email", "draft"]):
        # Email drafting: check for subject, greeting, body, closing, signature
        checks = 0
        if re.search(r"(?i)subject[:：]", answer):
            checks += 2
        if re.search(r"(?i)(dear|hello|hi|greetings)[\s,]", answer):
            checks += 2
        if re.search(r"(?i)(best regards|sincerely|regards|thanks)", answer):
            checks += 2
        if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", answer):
            checks += 2
        if len(answer) > 200:
            checks += 2
        scores["completeness"] = round(min(10, checks), 1)

    elif any(w in q_lower for w in ["买家", "buyer", "客户", "customer", "搜索"]):
        # Buyer search: check for company names, countries, emails, count
        checks = 0
        if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", answer):
            checks += 3
        if len(re.findall(r"\*\*[^*]+\*\*", answer)) >= 3:
            checks += 3  # Multiple bold company names
        if len(answer) > 300:
            checks += 2
        if re.search(r"🇩🇪|🇺🇸|🇫🇷|🇬🇧|🇯🇵|🇰🇷|Germany|USA|France|UK|Japan", answer):
            checks += 2
        scores["completeness"] = round(min(10, checks), 1)

    elif any(w in q_lower for w in ["汇率", "exchange", "rate"]):
        checks = 5
        if re.search(r"\d+\.\d+", answer):
            checks += 3
        if "CNY" in answer or "人民币" in answer:
            checks += 2
        scores["completeness"] = round(min(10, checks), 1)

    else:
        scores["completeness"] = 7 if len(answer) > 100 else 4

    # 3. Practicality
    has_actionable = bool(
        re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", answer)
        or re.search(r"(建议|推荐|可以|下一步|联系|contact|send|call)", answer)
    )
    scores["practicality"] = 8.0 if has_actionable else 5.0

    # 4. Language quality
    long_words = len([w for w in answer.split() if len(w) > 10])
    scores["language"] = 9.0 if long_words < 3 and len(answer) > 50 else 7.0

    # 5. Accuracy proxy: presence of specific data
    has_specifics = bool(
        re.search(r"\d{4}", answer)
        or re.search(r"\d+%", answer)
        or re.search(r"\$\d+|\d+\s*USD|\d+\s*CNY", answer)
        or re.search(r"CE|FCC|RoHS|ISO|UL|FDA", answer)
    )
    scores["accuracy"] = 8.0 if has_specifics else 6.0

    # Overall
    overall = sum(scores.values()) / len(scores)
    scores["overall"] = round(overall, 1)

    # Strengths
    if scores.get("completeness", 0) >= 8:
        strengths.append("信息完整，覆盖了关键要素")
    if scores.get("practicality", 0) >= 8:
        strengths.append("可直接执行，有明确的下一步")
    if scores.get("relevance", 0) >= 8:
        strengths.append("紧扣主题，直接回答了用户问题")
    if not strengths:
        strengths.append("回答基本回应了用户问题")

    # Weaknesses
    if scores.get("completeness", 0) < 6:
        weaknesses.append("缺少关键信息（如联系方式、具体数据）")
    if scores.get("practicality", 0) < 6:
        weaknesses.append("缺少可执行的具体建议")
    if len(answer) < 200:
        weaknesses.append("回答过于简短，缺少细节")
    if not weaknesses:
        weaknesses.append("无明显缺陷")

    # Suggestion
    tips = []
    if scores.get("completeness", 0) < 7:
        tips.append("补充更多具体信息如邮箱、公司名、数据等")
    if scores.get("practicality", 0) < 7:
        tips.append("增加可操作的建议（如下一步做什么）")
    if len(answer) < 150:
        tips.append("扩充回答内容，增加细节和例子")
    suggestion = "；".join(tips) if tips else "回答质量良好，无需改进"

    need_improve = overall < 7.5

    return {
        "scores": scores,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestion": suggestion,
        "need_improve": need_improve,
    }


def evaluate_response(question, answer):
    """
    GAN Discriminator: fast heuristic evaluation.
    Returns dict with scores, strengths, weaknesses, suggestion.
    Always returns a result (never None).
    """
    return heuristic_evaluate(question, answer)
