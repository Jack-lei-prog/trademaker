"""
简易 RAG 知识检索器
基于 TF-IDF 相似度匹配，从展会/认证/市场知识库检索相关内容
"""
import json
import re
from collections import Counter
import math


def _tokenize(text: str) -> list:
    """中英文混合分词"""
    text = text.lower()
    # 提取英文单词和中文字符
    en_words = re.findall(r'[a-z]{2,}', text)
    cn_chars = re.findall(r'[一-鿿]{1,2}', text)
    return en_words + cn_chars


def _tfidf_search(query: str, documents: list, top_k: int = 5) -> list:
    """TF-IDF 相似度搜索"""
    if not documents:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return documents[:top_k]

    # 构建文档词频
    doc_tokens = [_tokenize(d.get("text", "")) for d in documents]
    all_tokens = set(query_tokens)
    for dt in doc_tokens:
        all_tokens.update(dt)

    # TF-IDF
    N = len(documents)
    scores = []
    for i, dt in enumerate(doc_tokens):
        score = 0
        for token in query_tokens:
            if token in dt:
                tf = dt.count(token) / max(len(dt), 1)
                df = sum(1 for d in doc_tokens if token in d)
                idf = math.log((N + 1) / (df + 1)) + 1
                score += tf * idf
        if score > 0:
            scores.append((score, i))

    scores.sort(key=lambda x: x[0], reverse=True)
    return [documents[i] for _, i in scores[:top_k]]


def search_knowledge(query: str, top_k: int = 5) -> dict:
    """
    从知识库检索相关内容
    覆盖：展会、认证、市场洞察、外贸术语
    """
    from knowledge.tradeshows import TRADESHOWS, CERTIFICATIONS

    results = {"tradeshows": [], "certifications": [], "tips": []}

    # 搜索展会
    show_docs = []
    for key, shows in TRADESHOWS.items():
        for s in shows:
            show_docs.append({
                "text": f"{key} {s['name']} {s.get('name_cn','')} {s['location']} {s.get('focus','')}",
                "data": s
            })
    matched = _tfidf_search(query, show_docs, top_k)
    results["tradeshows"] = [m["data"] for m in matched]

    # 搜索认证
    cert_docs = []
    for key, certs in CERTIFICATIONS.items():
        for c in certs:
            cert_docs.append({
                "text": f"{key} {c['name']}",
                "data": c
            })
    matched = _tfidf_search(query, cert_docs, top_k)
    results["certifications"] = [m["data"] for m in matched]

    return results


# 外贸术语知识库
TRADE_TERMS = {
    "FOB": "Free On Board 离岸价 — 卖方负责将货物运至装运港并装上船，之后的风险和费用由买方承担",
    "CIF": "Cost Insurance Freight 到岸价 — 卖方承担运费和保险费，将货物运至目的港",
    "EXW": "Ex Works 工厂交货价 — 买方承担从卖方工厂起的所有费用和风险",
    "MOQ": "Minimum Order Quantity 最小起订量 — 供应商可接受的最小订单数量",
    "OEM": "Original Equipment Manufacturer 贴牌生产 — 按客户品牌生产产品",
    "ODM": "Original Design Manufacturer 原始设计制造商 — 供应商设计+生产，客户贴牌",
    "B2B": "Business to Business 企业对企业交易",
    "RFQ": "Request for Quotation 询价请求 — 买方向供应商索取报价",
    "PI": "Proforma Invoice 形式发票 — 出口前发给买方的预估发票",
    "BL": "Bill of Lading 提单 — 货物运输的物权凭证",
    "LC": "Letter of Credit 信用证 — 银行担保的支付方式",
    "T/T": "Telegraphic Transfer 电汇 — 国际汇款方式",
    "CE": "Conformité Européenne 欧盟强制性安全认证标志",
    "FCC": "Federal Communications Commission 美国无线设备强制认证",
    "RoHS": "Restriction of Hazardous Substances 欧盟有害物质限制指令",
    "REACH": "Registration Evaluation Authorisation of Chemicals 欧盟化学品注册",
    "HS Code": "Harmonized System Code 海关协调制度编码 — 国际贸易商品分类",
    "Incoterms": "International Commercial Terms 国际贸易术语 — 定义买卖双方责任/费用/风险",
}


def lookup_term(term: str) -> str:
    """查找外贸术语定义"""
    term_upper = term.upper().strip()
    if term_upper in TRADE_TERMS:
        return f"{term_upper}: {TRADE_TERMS[term_upper]}"
    # 模糊匹配
    for key, val in TRADE_TERMS.items():
        if key in term_upper:
            return f"{key}: {val}"
    return f"未找到术语 '{term}'"
