"""
外部数据源模块
为 tools.py 提供真实 API 数据，替代模拟数据
所有结果统一携带 source / source_url / fetched_at / confidence 字段
"""

import os
import json
import re
import threading
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

# ============================================================
# 数据溯源辅助函数
# ============================================================

def enrich_result(
    result: Dict[str, Any],
    source: str,
    source_url: str = "",
    confidence: float = 0.7,
) -> Dict[str, Any]:
    """为数据结构统一添加溯源字段，不覆盖已有值"""
    result.setdefault("source", source)
    result.setdefault("source_url", source_url)
    result.setdefault("fetched_at", datetime.now(timezone.utc).isoformat())
    result.setdefault("confidence", confidence)
    return result

# ============================================================
# 数据源健康状态（用于健康检查和降级提示）
# ============================================================
DATA_SOURCE_STATUS = {
    "wikidata": "ok",          # ok | degraded | failed
    "opencorporates": "ok",
    "llm_company": "ok",
    "exchange_rate": "ok",
}


# ============================================================
# 汇率数据源 — open.er-api.com（免费，无需 API Key）
# ============================================================
EXCHANGE_RATE_CACHE = {}  # 简单缓存，避免频繁请求
EXCHANGE_CACHE_TIME = None
_exchange_lock = threading.Lock()


def fetch_exchange_rates() -> Dict[str, Any]:
    """从 open.er-api.com 获取最新汇率数据（以 USD 为基准，线程安全）"""
    global EXCHANGE_RATE_CACHE, EXCHANGE_CACHE_TIME

    with _exchange_lock:
        # 缓存 1 小时
        if EXCHANGE_CACHE_TIME and (datetime.now() - EXCHANGE_CACHE_TIME).seconds < 3600:
            if EXCHANGE_RATE_CACHE:
                return EXCHANGE_RATE_CACHE

    try:
        resp = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("result") == "success":
                data = enrich_result(data, "open.er-api.com",
                                     "https://open.er-api.com/v6/latest/USD", 0.95)
                with _exchange_lock:
                    EXCHANGE_RATE_CACHE = data
                    EXCHANGE_CACHE_TIME = datetime.now()
                DATA_SOURCE_STATUS["exchange_rate"] = "ok"
                return data
    except Exception:
        pass

    DATA_SOURCE_STATUS["exchange_rate"] = "degraded"

    with _exchange_lock:
        return EXCHANGE_RATE_CACHE or None


# ============================================================
# 公司搜索 — 多重数据源（Wikidata → OpenCorporates → LLM 兜底）
# ============================================================
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
OPENCORP_API = "https://api.opencorporates.com/v0.4"


def search_companies_wikidata(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    通过 Wikidata 搜索公司实体（免费，全球可用）
    返回格式统一的公司列表
    """
    results = []
    try:
        params = {
            "action": "wbsearchentities",
            "search": query,
            "language": "en",
            "type": "item",
            "format": "json",
            "limit": min(limit, 50),
        }
        headers = {"User-Agent": "SW3_Agent_Trade/1.0"}
        resp = requests.get(WIKIDATA_API, params=params, headers=headers, timeout=3)
        if resp.status_code != 200:
            return results

        data = resp.json()
        items = data.get("search", [])
        if not items:
            return results

        # 批量获取实体详情（标签、描述、声明）
        entity_ids = [item["id"] for item in items[:limit]]
        params2 = {
            "action": "wbgetentities",
            "ids": "|".join(entity_ids),
            "props": "labels|descriptions|claims",
            "languages": "en|zh",
            "format": "json",
        }
        resp2 = requests.get(WIKIDATA_API, params=params2, headers=headers, timeout=3)
        if resp2.status_code != 200:
            # 无详情时仍返回搜索结果
            for item in items[:limit]:
                wd_id = item.get("id", "")
                wd_url = item.get("url", f"https://www.wikidata.org/wiki/{wd_id}")
                results.append(enrich_result({
                    "company_name": item.get("label", wd_id or "Unknown"),
                    "description": item.get("description", ""),
                    "wikidata_id": wd_id,
                    "wikidata_url": wd_url,
                    "industry": "Unknown",
                    "headquarters": "Unknown",
                }, "Wikidata", wd_url, 0.80))
            return results

        entities = (resp2.json().get("entities", {}) or {})

        for entity_id, entity in entities.items():
            labels = entity.get("labels", {})
            descriptions = entity.get("descriptions", {})
            claims = entity.get("claims", {})

            name = labels.get("en", {}).get("value") or labels.get("zh", {}).get("value") or entity_id
            desc = descriptions.get("en", {}).get("value") or descriptions.get("zh", {}).get("value") or ""

            # 从 Wikidata 声明中提取行业和总部（P452=行业, P159=总部, P17=国家）
            industry = "Unknown"
            headquarters = "Unknown"

            for claim_list in claims.values():
                for claim in claim_list:
                    mainsnak = claim.get("mainsnak", {})
                    prop_id = claim.get("mainsnak", {}).get("property", "")
                    datavalue = mainsnak.get("datavalue", {})

                    if not datavalue:
                        continue

                    value = datavalue.get("value", {})

                    # 尝试提取行业描述
                    if isinstance(value, dict) and "id" in value and value["id"].startswith("Q"):
                        # 可能是行业类别 - 先记录
                        pass

            wd_url = f"https://www.wikidata.org/wiki/{entity_id}"
            results.append(enrich_result({
                "company_name": name,
                "description": desc,
                "wikidata_id": entity_id,
                "wikidata_url": wd_url,
                "industry": industry,
                "headquarters": headquarters,
            }, "Wikidata", wd_url, 0.80))

    except Exception:
        DATA_SOURCE_STATUS["wikidata"] = "degraded"
    else:
        DATA_SOURCE_STATUS["wikidata"] = "ok" if results else "degraded"
    return results


def search_companies_opencorp(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """通过 OpenCorporates 搜索公司"""
    results = []
    try:
        url = f"{OPENCORP_API}/companies/search"
        resp = requests.get(url, params={"q": query}, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            companies = (data.get("results", {}) or {}).get("companies", [])
            for item in companies[:limit]:
                c = item.get("company", {})
                oc_url = c.get("opencorporates_url", "")
                results.append(enrich_result({
                    "company_name": c.get("name", "Unknown"),
                    "jurisdiction": c.get("jurisdiction_code", "").upper(),
                    "company_number": c.get("company_number", ""),
                    "status": c.get("current_status", "Unknown"),
                    "registered_address": c.get("registered_address_in_full", ""),
                    "company_type": c.get("company_type", ""),
                    "opencorporates_url": oc_url,
                }, "OpenCorporates", oc_url, 0.85))
            DATA_SOURCE_STATUS["opencorporates"] = "ok"
    except Exception:
        DATA_SOURCE_STATUS["opencorporates"] = "degraded"
    return results


def search_companies_llm(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    用 LLM 生成潜在买家/进口商/分销商列表
    专为外贸场景优化：包含公司名、网站、联系邮箱等
    """
    system = (
        "You are a global trade database. List real companies that import, distribute, or buy this product."
    )
    user = (
        f"List {limit} real companies worldwide that import, distribute, or buy: {query}.\n"
        "Return ONLY a JSON array. Each object: company_name, country, website, email, "
        "what_they_buy (1 line), why_relevant (1 line), type (importer/distributor/wholesaler/retailer/manufacturer).\n"
        "For email: if you know the company's actual procurement/contact email, provide it. "
        "Otherwise use common patterns like purchasing@website, info@website, sales@website, or inquiry@website based on their domain.\n"
        "IMPORTANT: always include an email field for every company."
    )
    result = call_llm(system, user, max_tokens=2000, timeout=25)
    if result:
        try:
            text = result.strip()
            # 清理 markdown 代码块
            if text.startswith("```"):
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines)
            companies = json.loads(text)
            if isinstance(companies, list):
                DATA_SOURCE_STATUS["llm_company"] = "ok"
                return [enrich_result({
                    "company_name": c.get("company_name", "Unknown"),
                    "jurisdiction": c.get("country", "Unknown"),
                    "industry": query,
                    "website": c.get("website", ""),
                    "email": c.get("email", ""),
                    "what_they_buy": c.get("what_they_buy", ""),
                    "why_relevant": c.get("why_relevant", ""),
                    "buyer_type": c.get("type", ""),
                    "description": c.get("why_relevant", c.get("description", "")),
                }, "LLM-generated", "", 0.50) for c in companies[:limit]]
        except json.JSONDecodeError:
            pass
    DATA_SOURCE_STATUS["llm_company"] = "degraded"
    return []


def _expand_trade_terms(keyword: str) -> List[str]:
    """
    智能扩展贸易搜索词：将简单的产品名扩展为贸易相关搜索词
    示例: "IGBT" → ["IGBT", "IGBT distributor", "IGBT importer", "IGBT module manufacturer", ...]
    """
    terms = [keyword]

    # 去掉中文字符，提取纯英文 token 和核心中文
    english_tokens = re.findall(r'[A-Za-z0-9]{2,}', keyword)
    chinese_parts = re.findall(r'[一-龥]+', keyword)

    # 中文关键词映射（行业 → 英文）
    cn_to_en = {
        "电子": "electronics", "手机": "smartphone", "电脑": "computer",
        "服装": "clothing", "纺织": "textile", "机械": "machinery",
        "化工": "chemical", "食品": "food", "医药": "pharmaceutical",
        "汽车": "automotive", "家具": "furniture", "玩具": "toy",
        "塑料": "plastic", "钢铁": "steel", "灯具": "lighting",
        "鞋": "footwear", "包": "bag", "珠宝": "jewelry",
        "太阳能": "solar", "电池": "battery", "芯片": "semiconductor",
        "IGBT": "semiconductor", "LED": "lighting", "PCB": "printed circuit board",
        "家电": "home appliance", "工具": "tools", "五金": "hardware",
        "医疗器械": "medical device", "化妆品": "cosmetics",
        "农产品": "agricultural products", "建材": "building materials",
    }

    # 从中文部分找英文对应词
    base_english_terms = list(english_tokens)
    for cn_part in chinese_parts:
        for cn_key, en_val in cn_to_en.items():
            if cn_key in cn_part and en_val not in base_english_terms:
                base_english_terms.append(en_val)

    # 如果没有英文词，用原始关键词的全拼
    if not base_english_terms:
        # 纯中文关键词，尝试整体映射
        for cn_key, en_val in cn_to_en.items():
            if cn_key in keyword and en_val not in base_english_terms:
                base_english_terms.append(en_val)
        if not base_english_terms:
            base_english_terms = [keyword]  # fallback

    # 对每个英文基础词，追加贸易后缀
    trade_suffixes = [
        "distributor", "importer", "wholesaler", "buyer",
        "manufacturer", "supplier", "trader",
    ]

    for base in base_english_terms:
        base_lower = base.lower().strip()
        if base_lower not in [t.lower() for t in terms]:
            terms.append(base)
        # 追加贸易词组合
        for suffix in trade_suffixes:
            combined = f"{base} {suffix}"
            if combined.lower() not in [t.lower() for t in terms]:
                terms.append(combined)

    # 也尝试用原始关键词（含中文）直接组词
    if chinese_parts and base_english_terms:
        for suffix in trade_suffixes:
            for base in base_english_terms[:2]:  # 限制组合数量
                combined = f"{base} {suffix}"
                if combined.lower() not in [t.lower() for t in terms]:
                    terms.append(combined)

    return terms


def get_company_detail_opencorp(jurisdiction: str, company_number: str) -> Optional[Dict[str, Any]]:
    """获取 OpenCorporates 中某公司的详细信息"""
    try:
        url = f"{OPENCORP_API}/companies/{jurisdiction}/{company_number}"
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            c = (data.get("results", {}) or {}).get("company", {})
            if c:
                oc_url = c.get("opencorporates_url", "")
                return enrich_result({
                    "company_name": c.get("name", "Unknown"),
                    "jurisdiction": c.get("jurisdiction_code", "").upper(),
                    "status": c.get("current_status", ""),
                    "registered_address": c.get("registered_address_in_full", ""),
                    "company_type": c.get("company_type", ""),
                    "incorporation_date": c.get("incorporation_date", ""),
                    "officers": [
                        {
                            "name": o.get("officer", {}).get("name", ""),
                            "position": o.get("officer", {}).get("position", ""),
                        }
                        for o in (c.get("officers", []) or [])[:5]
                    ],
                    "industry_codes": c.get("industry_codes", []),
                    "opencorporates_url": oc_url,
                }, "OpenCorporates", oc_url, 0.85)
    except Exception:
        pass
    return None


# ============================================================
# LLM 生成工具 — 复用 SynScale API
# ============================================================
_llm_session = None


def _get_llm_session():
    """获取或创建 LLM 专用共享 Session（绕过系统代理）"""
    global _llm_session
    if _llm_session is None:
        _llm_session = requests.Session()
        _llm_session.trust_env = False  # 绕过系统代理直连
    return _llm_session


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 2000, timeout: int = 25) -> Optional[str]:
    """调用 LLM API 生成文本 — 多提供商自动切换"""
    from services import LLM_PROVIDERS
    if not LLM_PROVIDERS:
        return None

    session = _get_llm_session()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for provider in LLM_PROVIDERS:
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {provider['key']}",
            }
            payload = {
                "model": provider["model"],
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": max_tokens,
            }
            resp = session.post(provider["url"], headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {})
                    result = msg.get("content", "") or msg.get("reasoning_content", "")
                    if result and ("We are asked" in result[:50] or "The user" in result[:50]):
                        lines = result.strip().split("\n")
                        for line in reversed(lines):
                            line = line.strip()
                            if line and not line.startswith(("We", "The user", "Let", "First", "I need", "This is", "So we")):
                                return line
                        return result.strip().rsplit(".", 2)[0] + "."
                    return result
            elif resp.status_code < 500:
                break  # 4xx 不重试
        except Exception as e:
            print(f"[call_llm error] provider={provider['name']}: {e}")
            continue  # 尝试下一个 provider
    return None