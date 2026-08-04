"""
多 Agent 协作系统 — 4 个专业 Agent + 1 个协调者
"""
from tools import TOOL_DESCRIPTIONS, TOOL_FUNCTIONS

AGENTS = {
    "coordinator": {
        "name": "协调者",
        "emoji": "🎯",
        "role": "分析用户意图，决定派遣哪个或哪些专业Agent处理任务。",
        "tools": [],
    },
    "buyer_agent": {
        "name": "买家搜索Agent",
        "emoji": "🔍",
        "role": "全球买家搜索专家。多数据源搜索，绝不编造邮箱。",
        "tools": ["search_buyers", "analyze_company", "search_trade_knowledge"],
    },
    "email_agent": {
        "name": "邮件撰写Agent",
        "emoji": "✉️",
        "role": "B2B开发信和商务邮件专家。生成个性化开发信、客服回复。",
        "tools": ["draft_email", "send_email", "draft_customer_reply"],
    },
    "trade_agent": {
        "name": "展会情报Agent",
        "emoji": "📅",
        "role": "全球展会情报和市场分析专家。匹配展会、查询认证、生成广告语。",
        "tools": ["search_trade_knowledge", "query_exchange_rate",
                  "generate_product_desc", "write_marketing_slogan"],
    },
    "inquiry_agent": {
        "name": "询盘处理Agent",
        "emoji": "📬",
        "role": "客户询盘处理专家。提取信息、分类意图、生成回复。",
        "tools": ["process_inquiry"],
    },
    "dashboard_agent": {
        "name": "数据分析Agent",
        "emoji": "📊",
        "role": "销售数据和邮件状态分析专家。",
        "tools": ["analyze_daily_sales", "check_email_status"],
    },
}

INTENT_ROUTES = {
    "搜索": "buyer_agent",
    "买家": "buyer_agent",
    "进口商": "buyer_agent",
    "分销商": "buyer_agent",
    "公司": "buyer_agent",
    "开发信": "email_agent",
    "写邮件": "email_agent",
    "发邮件": "email_agent",
    "客服": "email_agent",
    "回复": "email_agent",
    "展会": "trade_agent",
    "认证": "trade_agent",
    "汇率": "trade_agent",
    "广告语": "trade_agent",
    "商品描述": "trade_agent",
    "产品描述": "trade_agent",
    "市场": "trade_agent",
    "询盘": "inquiry_agent",
    "询价": "inquiry_agent",
    "销售": "dashboard_agent",
    "日报": "dashboard_agent",
    "跟进": "dashboard_agent",
    "统计": "dashboard_agent",
}

MULTI_AGENT_PROMPT = """# TradeMaster 多 Agent 协作系统

你是 TradeMaster 外贸通的多Agent协调系统。根据用户意图，你将切换到对应的专业Agent角色：

## Agent 团队
- 🔍 买家搜索Agent — 搜索全球买家、分析公司背景、知识库检索
- ✉️ 邮件撰写Agent — 开发信、客服回复、邮件发送
- 📅 展会情报Agent — 展会匹配、认证查询、汇率、广告语、产品描述
- 📬 询盘处理Agent — 客户询盘提取、分类、回复、跟进
- 📊 数据分析Agent — 销售分析、邮件状态检查

## 工作流程
1. 分析用户意图 → 确定应该由哪个Agent处理
2. 以该Agent的身份回复（在回复开头标注 Agent 名称和emoji，如 "🔍 买家搜索Agent 已启动"）
3. 调用对应的 Function Calling 工具
4. 如果任务需要多个Agent协作（如"搜索买家然后写开发信"），依次完成

## 示例
用户："搜索德国LED进口商"
→ 🔍 买家搜索Agent 已启动 → 调用 search_buyers → 返回结果

用户："搜索德国LED进口商并给他们写开发信"
→ 🔍 买家搜索Agent 先搜索 → 返回买家清单 → ✉️ 邮件撰写Agent 接着写开发信
"""

def get_agent_tools(agent_id: str) -> list:
    if agent_id not in AGENTS:
        return TOOL_DESCRIPTIONS
    tool_names = AGENTS[agent_id].get("tools", [])
    if not tool_names:
        return TOOL_DESCRIPTIONS
    return [t for t in TOOL_DESCRIPTIONS
            if t["function"]["name"] in tool_names]

def detect_intent(user_input: str) -> str:
    for keyword, agent_id in INTENT_ROUTES.items():
        if keyword in user_input:
            return agent_id
    return "coordinator"
