"""
Skill 3: 展会情报与市场洞察 (Trade Intelligence)
───────────────────────────────────────────────
按产品类别匹配全球展会 + 出口认证要求 + 市场趋势分析。
数据覆盖：消费电子/LED/服装/家具/太阳能/玩具/医疗/化工等品类
"""


class TradeIntelligenceSkill:
    name = "展会情报与市场洞察"
    name_en = "Trade Intelligence"
    description = "按产品匹配全球展会(50+真实展会数据) + 出口强制认证清单 + 市场趋势洞察"
    version = "1.0"
    tools = ["query_exchange_rate", "generate_product_desc", "write_marketing_slogan"]
    knowledge = ["knowledge/tradeshows.py"]

    # 覆盖品类
    CATEGORIES = [
        "bluetooth earphone", "led light", "clothing", "furniture",
        "phone case", "home appliance", "solar", "toy",
        "medical device", "chemical",
    ]

    @staticmethod
    def get_rules():
        return """
# 展会推荐规则
1. 根据用户产品关键词智能匹配全球展会
2. 展示展会名称/时间/地点/规模/参展建议/官网链接
3. 附带出口认证清单（强制/可选，费用，周期）
4. 附带市场趋势洞察（规模/增长/定价策略）
"""
