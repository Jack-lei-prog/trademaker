"""
Skill 4: 询盘处理 (Inquiry Processing)
─────────────────────────────────────
完整询盘处理5步闭环：
提取客户信息 → 意图分类 → 背景调研 → 生成个性化回复 → 加入跟进队列
"""


class InquiryProcessingSkill:
    name = "询盘处理"
    name_en = "Inquiry Processing"
    description = "5步询盘闭环：自动提取客户信息→意图分类(采购/比价/调研/垃圾)→公司背景调研→AI生成个性化回复→48h自动跟进提醒"
    version = "1.0"
    tools = ["process_inquiry", "draft_customer_reply"]

    INTENT_TYPES = {
        "genuine_purchase": {"label": "真实采购", "urgency": "high", "strategy": "速报价+产品规格+MOQ"},
        "price_shopping": {"label": "比价询价", "urgency": "medium", "strategy": "强调差异化+先建信任"},
        "market_research": {"label": "市场调研", "urgency": "low", "strategy": "产品资料+行业分析"},
        "spam": {"label": "垃圾询盘", "urgency": "ignore", "strategy": "简短回复或忽略"},
    }

    @staticmethod
    def get_rules():
        return """
# 询盘处理流程
1. extract_client_info — 提取公司/邮箱/国家/产品
2. classify_inquiry — LLM分类+关键词降级
3. fetch_background — OpenCorporates/Wikidata搜索
4. generate_reply — 个性化回复（英文/中文自适应）
5. add_to_followup — 48h未回复自动提醒
"""
