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
# 注: .env 已在 app.py 入口处加载(override=True)

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


# ============================================================
# Kimi 深度评价 (Moonshot AI)
# ============================================================

KIMI_API_KEY = os.getenv("KIMI_API_KEY") or os.getenv("LLM_API_KEY") or ""
KIMI_API_URL = "https://api.moonshot.cn/v1/chat/completions"
KIMI_MODEL = os.getenv("KIMI_MODEL") or os.getenv("LLM_MODEL") or "kimi-k2.7-code"


def kimi_available():
    """检查 Kimi API 是否已配置"""
    return bool(KIMI_API_KEY and "your-kimi-key" not in KIMI_API_KEY)


def kimi_evaluate(question: str, answer: str) -> dict:
    """
    调用 Kimi (Moonshot AI) 对 TradeMaster 的回答做深度评价。
    返回与 heuristic_evaluate 相同格式的 dict。
    """
    if not kimi_available():
        return {"error": "Kimi API Key 未配置，请在 .env 中设置 KIMI_API_KEY", "scores": {}}

    system = """你是一个专业的外贸 AI 助手评价专家。直接输出 JSON，不要推理过程。

评分维度（每个 1-10 分）：
1. relevance(相关性) 2. accuracy(准确性) 3. completeness(完整性)
4. practicality(实用性) 5. language(语言质量) 6. overall(综合)

同时给出 2-3 条优点(strengths)、2-3 条缺点(weaknesses)、1 条改进建议(suggestion)。
综合评分 < 8 时 need_improve 为 true。

直接输出 JSON：{"scores":{"relevance":8,"accuracy":7,"completeness":6,"practicality":8,"language":9,"overall":7.5},"strengths":["优1","优2"],"weaknesses":["缺1","缺2"],"suggestion":"建议","need_improve":true}"""

    user = f"问题：{question[:1000]}\n\n回答：{answer[:2000]}\n\n输出JSON："

    try:
        resp = requests.post(
            KIMI_API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {KIMI_API_KEY}",
            },
            json={
                "model": KIMI_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 1.0,  # Kimi 推理模型需要 temperature=1
                "max_tokens": 2000,
            },
            timeout=30,
        )

        if resp.status_code != 200:
            return {"error": f"Kimi API {resp.status_code}: {resp.text[:200]}", "scores": {}}

        data = resp.json()
        msg = data["choices"][0]["message"]
        content = msg.get("content", "") or msg.get("reasoning_content", "")

        # 如果 content 为空（纯推理模型），尝试从 reasoning 尾部提取 JSON
        if not content.strip():
            reasoning = msg.get("reasoning_content", "")
            # 从尾部找 JSON
            import re as _re
            m = _re.search(r'\{[^{}]*"scores"[^{}]*\}', reasoning)
            if m:
                content = m.group(0)

        # 清理 markdown
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)

        result = json.loads(content)

        # 确保所有字段存在
        if "scores" not in result:
            result["scores"] = {}
        if "strengths" not in result:
            result["strengths"] = []
        if "weaknesses" not in result:
            result["weaknesses"] = []
        if "suggestion" not in result:
            result["suggestion"] = ""
        if "need_improve" not in result:
            overall = float(result.get("scores", {}).get("overall", 5))
            result["need_improve"] = overall < 8.0

        return result

    except requests.exceptions.Timeout:
        return {"error": "Kimi API 请求超时，请稍后重试", "scores": {}}
    except json.JSONDecodeError:
        return {"error": f"Kimi 返回格式异常: {content[:200]}", "scores": {}}
    except Exception as e:
        return {"error": f"Kimi 评价出错: {str(e)}", "scores": {}}


def dual_evaluate(question: str, answer: str) -> dict:
    """
    双评价：启发式（快速） + Kimi（深度）
    返回包含两者的 dict
    """
    heuristic = heuristic_evaluate(question, answer)
    kimi = kimi_evaluate(question, answer) if kimi_available() else {"error": "Kimi 未配置"}
    return {
        "heuristic": heuristic,
        "kimi": kimi,
    }
