"""
Skill 1: 买家搜索 (Buyer Search)
─────────────────────────────────
多数据源协同搜索全球进口商/分销商/批发商。
数据源：Wikidata → OpenCorporates → LLM补充
输出：公司名 + 国家 + 网站 + 邮箱(标注验证状态) + 采购类型 + 推荐理由
"""


class BuyerSearchSkill:
    name = "买家搜索"
    name_en = "Buyer Search"
    description = "全球买家智能搜索：多数据源(Wikidata/OpenCorporates/LLM)协同，输出结构化的潜在客户清单"
    version = "1.0"
    tools = ["search_buyers", "analyze_company"]

    # 大企业供应商门户（禁止推测邮箱）
    ENTERPRISE_PORTALS = {
        "IKEA": "https://supplier.ikea.com",
        "Walmart": "https://walmart.com/suppliers",
        "Amazon": "https://sell.amazon.com",
        "Home Depot": "https://homedepot.com/suppliers",
        "Target": "https://corporate.target.com/suppliers",
        "Costco": "https://costco.com/supplier-diversity.html",
        "Best Buy": "https://bestbuy.com/suppliers",
        "Carrefour": "https://carrefour.com/suppliers",
        "Tesco": "https://tesco.com/suppliers",
        "Aldi": "https://aldi.com/suppliers",
        "Lidl": "https://lidl.com/suppliers",
        "Metro AG": "https://metro-group.com/suppliers",
        "Auchan": "https://auchan-retail.com/suppliers",
        "Lowe's": "https://lowes.com/suppliers",
        "Danone": "https://danone.com/suppliers",
    }

    @staticmethod
    def get_rules():
        return """
# 买家搜索规则
1. 数据库匹配优先 — 先列出 structured_results 中的真实数据
2. 大企业 → 不推测邮箱，给出供应商注册URL
3. 中小公司 → 可推测邮箱但必须标注 ⚠️未验证
4. 补充建议：LinkedIn搜索关键词 + B2B平台RFQ + 行业展会
5. 邮箱分三级标注：✅验证 ⚠️未验证 ❌不可用
"""
