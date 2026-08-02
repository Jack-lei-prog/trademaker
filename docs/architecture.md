# 技术架构文档

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (HTML/CSS/JS)                  │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  index.html - 单文件应用                              │ │
│  │  - 聊天UI                                           │ │
│  │  - Markdown渲染                                     │ │
│  │  - 快捷操作按钮                                     │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP (REST API)
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 Flask Server (app.py:5000)                │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Routes:                                            │ │
│  │  - GET  /          → 渲染聊天界面                   │ │
│  │  - POST /api/chat  → 对话API                        │ │
│  │  - POST /api/clear → 清空会话                       │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Agent Loop (run_agent):                            │ │
│  │  - 迭代调用 LLM (最多5轮)                           │ │
│  │  - 检测 tool_calls 并执行                           │ │
│  │  - 管理会话历史                                     │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP (OpenAI-compatible API)
                       ▼
┌─────────────────────────────────────────────────────────┐
│         SynScale API (synscale.onesyn.ai/v1)             │
│  - Model: deepseek-v4-pro                                │
│  - Function Calling support                              │
└─────────────────────────────────────────────────────────┘
```

## 模块职责

### app.py — 应用主入口
- Flask 路由注册 (GET `/`, POST `/api/chat`, POST `/api/clear`)
- Agent 循环逻辑 `run_agent()`
- API 调用 `call_synscale()` — 封装 LLM 请求，包含重试逻辑
- 工具执行 `execute_tool()` — 调用 tools.py 中的对应函数
- 会话管理 `chat_history` — 内存字典，key 为 session_id

### prompts.py — 系统提示词
- `SYSTEM_PROMPT` — 定义 AI 角色、可用工具、行为规则

### tools.py — 工具定义与实现
- `TOOL_DESCRIPTIONS` — Function Calling 工具 schema (8个工具)
- `TOOL_FUNCTIONS` — 工具函数映射字典
- 每个工具函数调用 data_sources.py 获取数据

### data_sources.py — 数据源
- 模拟数据库：买家、公司、汇率、商品描述、邮件模板
- 返回结构化 JSON 数据
- 标注数据来源 (Mock Data / Wikidata)

### templates/index.html — 前端UI
- 纯 HTML/CSS/JS 单文件，无框架依赖
- Markdown 渲染引擎 (formatMarkdown)
- 快捷操作按钮 (appendFollowUpButtons)
- 空白元素清理 (cleanEmptyElements)
- 建议提取 (extractSuggestions)

## 数据流

```
用户输入 → POST /api/chat → run_agent()
  → call_synscale(messages, tools)
    → 检测 tool_calls
      → 是: execute_tool() → 结果追加到 messages → 继续循环
      → 否: 返回 assistant content
  → 返回 JSON { reply, tool_calls }
→ 前端渲染 Markdown + 后续操作按钮
```

## 会话管理
- 会话存储在内存 `chat_history` 字典
- 每个 session 最多保留 15 条消息（不含 system prompt）
- 服务重启后会话丢失

## API 调用策略
- 超时时间: 60 秒
- 温度参数: 0.6
- max_tokens: 2000
- tool_choice: "auto"
- 错误处理: 捕获 requests 异常，返回友好错误消息