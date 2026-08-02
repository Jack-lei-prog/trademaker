# 项目需求文档

## 项目名称
外贸通 (TradeMaster) - 智能外贸业务助理

## 项目概述
基于大语言模型的智能外贸业务助理Web应用，帮助外贸业务员完成客户开发、市场调研、业务沟通等日常任务。

## 核心功能

### 1. 智能对话
- 支持自然语言交互，理解外贸业务场景
- 多轮对话上下文记忆
- 流式打字动画反馈

### 2. 工具调用 (Function Calling)
- **搜索买家** `search_buyers(keyword)` — 根据关键词搜索潜在买家
- **分析公司** `analyze_company(domain)` — 分析公司背景信息
- **生成开发信** `draft_email(company_info, product_highlight)` — 生成英文开发信
- **查询汇率** `query_exchange_rate(currency)` — 查询实时汇率
- **商品描述** `generate_product_desc(name, tone, target_audience)` — 生成商品标题/卖点/描述
- **起草回复** `draft_customer_reply(message, order_status)` — 根据客户消息生成回复
- **销售日报** `analyze_daily_sales(orders_summary)` — 分析销售数据生成日报
- **广告语** `write_marketing_slogan(promotion_topic)` — 生成营销广告语

### 3. Web界面
- 响应式聊天界面，支持PC和移动端
- 快捷操作按钮
- Markdown格式渲染（表格、列表、代码块、粗体等）
- 会话清空功能
- 所有回复后自动展示后续操作建议

## 非功能需求
- API调用超时60秒
- 工具调用最多迭代5轮
- 会话历史保留最近15条消息
- 回答精简，控制在150字以内
- 开发信100字以内

## 技术栈
- **后端**: Python 3.x + Flask
- **前端**: 原生HTML/CSS/JS，单文件模板
- **AI服务**: DeepSeek V4 Pro (via SynScale API)
- **数据源**: 模拟数据 (data_sources.py)

## 版本
- 当前版本: v1.0.0
- 更新日期: 2026-07-30