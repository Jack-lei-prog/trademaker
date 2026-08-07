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

你是 TradeMaster 外贸通的多Agent协调系统。根据用户意图，你将依次切换到对应的专业Agent角色完成任务。

## Agent 团队
- 🔍 买家搜索Agent — 搜索全球买家、分析公司背景、知识库检索
- ✉️ 邮件撰写Agent — 开发信、客服回复、邮件发送
- 📅 展会情报Agent — 展会匹配、认证查询、汇率、广告语、产品描述
- 📬 询盘处理Agent — 客户询盘提取、分类、回复、跟进
- 📊 数据分析Agent — 销售分析、邮件状态检查

## 多步骤任务编排规则
1. 如果用户请求包含多个步骤（如"搜索X买家并给他们写开发信"），你必须按顺序执行
2. 第一步用对应Agent的工具完成任务，获得结果
3. 在回复中明确标注当前Agent（如"🔍 买家搜索Agent 已启动"）
4. 如果下一步需要不同Agent的工具，在回复中标注切换（如"→ ✉️ 邮件撰写Agent 接手"），然后调用该Agent的工具
5. 每个Agent只能使用自己的工具子集。coordinator 拥有全部工具
6. 如果当前Agent没有所需工具，必须由 coordinator 角色调用

## 每个Agent可用工具
- 🔍 buyer_agent: search_buyers, analyze_company, search_trade_knowledge
- ✉️ email_agent: draft_email, send_email, draft_customer_reply
- 📅 trade_agent: search_trade_knowledge, query_exchange_rate, generate_product_desc, write_marketing_slogan
- 📬 inquiry_agent: process_inquiry
- 📊 dashboard_agent: analyze_daily_sales, check_email_status
- 🎯 coordinator: 全部工具

## 示例
用户："搜索德国LED进口商并给他们写开发信"
→ 🔍 买家搜索Agent 已启动 → 调用 search_buyers("LED") → 得到买家列表
→ ✉️ 邮件撰写Agent 已启动 → 调用 draft_email(买家1的info, 产品亮点) → 返回开发信
→ 完成，向用户展示搜索到的买家列表和对应的开发信
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
    """返回主要意图（向后兼容）"""
    for keyword, agent_id in INTENT_ROUTES.items():
        if keyword in user_input:
            return agent_id
    return "coordinator"


def detect_intents(user_input: str) -> list:
    """
    检测用户请求中的所有意图（按出现顺序）。
    返回: [(agent_id, keyword, position), ...]
    用于多步骤任务编排。
    """
    matches = []
    for keyword, agent_id in INTENT_ROUTES.items():
        pos = user_input.find(keyword)
        if pos >= 0:
            matches.append((agent_id, keyword, pos))
    if not matches:
        return [("coordinator", "", 0)]
    matches.sort(key=lambda x: x[2])  # 按出现位置排序
    # 去重（同一个 agent 只保留第一次出现）
    seen = set()
    result = []
    for agent_id, kw, pos in matches:
        if agent_id not in seen:
            seen.add(agent_id)
            result.append((agent_id, kw, pos))
    # coordinator 始终有全部工具，不要重复
    if len(result) == 1 and result[0][0] == "buyer_agent":
        # 仅搜索请求 -> buyer_agent 有搜索工具
        pass
    return result


def get_task_agents(user_input: str) -> list:
    """
    多步骤任务计划：拆解用户请求为子任务，每个子任务绑定 agent。
    返回: [{"agent_id": "buyer_agent", "step": 1, "description": "..."}, ...]
    """
    intents = detect_intents(user_input)
    if not intents:
        return [{"agent_id": "coordinator", "step": 1, "description": "处理用户请求"}]
    tasks = []
    for i, (agent_id, keyword, _) in enumerate(intents):
        agent_info = AGENTS.get(agent_id, AGENTS["coordinator"])
        task_content = user_input.split(keyword, 1)[1] if i > 0 else user_input
        tasks.append({
            "agent_id": agent_id,
            "agent_name": agent_info["name"],
            "agent_emoji": agent_info["emoji"],
            "step": i + 1,
            "description": task_content[:80],
        })
    return tasks
