# CLAUDE.md - AI 开发指南

## 项目概述
**外贸通 (TradeMaster)** — 基于大语言模型的多 Agent 智能外贸业务助理 Web 应用。12 个 Function Calling 工具 + 6 个协作 Agent + RAG 知识库。

## 快速启动
```bash
# 1. 配 .env（确保 SECRET_KEY + LLM_API_KEY）
cp .env.example .env && nano .env

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动
python app.py
# 访问 http://127.0.0.1:5000

# 4. 测试
pytest tests/ -v --ignore=tests/test_e2e.py
```

## 标准文件路径

### 项目核心文件
| 文件 | 说明 |
|------|------|
| `app.py` | Flask 主入口 — Blueprint 注册、CORS 白名单、安全响应头 |
| `config.py` | 集中配置 — SECRET_KEY 校验、CORS_ORIGINS、LLM 提供商 |
| `services.py` | Agent 循环 + 多 LLM 提供商故障切换 |
| `tools.py` | 12 个 Function Calling 工具 schema 与实现 |
| `data_sources.py` | 外部数据源 — Wikidata / OpenCorporates / open.er-api / LLM |
| `prompts.py` | 系统提示词 (SYSTEM_PROMPT) |
| `prompt_service.py` | 提示词构建器 — 用户上下文 + 产品手册注入 |
| `agents.py` | 6 个协作 Agent + intent 路由 + 工具子集分配 |
| `templates/index.html` | 单文件 SPA 前端 |
| `.env` | API Key / SECRET_KEY / SMTP 等敏感配置 |
| `.env.example` | 环境变量模板 |

### 安全模块
| 文件 | 说明 |
|------|------|
| `auth_middleware.py` | JWT 认证 — create_token / decode_token / @login_required / @optional_login |
| `security.py` | 速率限制 (RateLimitStore 抽象) + 输入校验 (validate_input) |
| `smtp_crypto.py` | Fernet 对称加密 — SMTP 密码加密存储 |
| `logger.py` | 结构化日志 + SensitiveDataFilter 敏感数据脱敏 |

### 数据模块
| 文件 | 说明 |
|------|------|
| `db.py` | SQLite — WAL 模式、线程安全连接池、Session/KV/Contacts CRUD |
| `user_service.py` | 用户认证 — bcrypt 密码哈希、_safe_str |
| `mailer.py` | SMTP 邮件发送 — QQ邮箱 / Gmail / 通用 SMTP |
| `smtp_config.py` | SMTP 配置管理 — 密码加密存储到 SQLite KV |
| `email_tracker.py` | 邮件追踪像素 + 意图分类 |
| `imap_sync.py` | IMAP 收件箱同步 |
| `inquiry_engine.py` | 询盘处理引擎 — 5步闭环 |
| `evaluator.py` | GAN 双评价器 — 启发式 + Kimi |

### Blueprints `blueprints/`
| 文件 | 端点 | 认证 |
|------|------|------|
| `auth_bp.py` | /api/register, /api/login | — (返回 JWT) |
| `chat_bp.py` | /api/chat, /api/chat/stream, /api/health, /api/upload/* | — |
| `email_bp.py` | /api/email/draft, /api/email/smtp_*, /api/emails/* | ✅ JWT |
| `inquiry_bp.py` | /api/inquiry/* | ✅ JWT |
| `evaluate_bp.py` | /api/evaluate, /api/evaluate/kimi, /api/evaluate/dual | ✅ JWT |
| `contact_bp.py` | /api/contacts/* | ✅ JWT |
| `dashboard_bp.py` | /api/dashboard, /api/workflow/*, /api/preferences | ✅ JWT |
| `doll_bp.py` | /api/doll/* | — |

### Skills `skills/`
6 个声明式 Skill 容器: `buyer_search` / `email_draft` / `trade_intelligence` / `inquiry_processing` / `email_tracking` / `contact_management`

### 知识库 `knowledge/`
- `tradeshows.py` — 50+ 全球展会数据库
- `retriever.py` — TF-IDF 语义检索器
- `demo.py` — Demo 账号初始化 (demo@trademaster.com / demo2024)

### 文档目录 `docs/`
| 文件 | 说明 |
|------|------|
| `requirements.md` | 功能需求 + 非功能需求 + 技术栈 |
| `architecture.md` | 系统架构图、模块职责、数据流 |
| `coding-standards.md` | Python/JS/HTML/CSS/Git 规范 |
| `development-workflow.md` | 每日流程、环境配置、常见任务 |

### 开发日志 `devlog/`
每日日志: `devlog/YYYY-MM-DD.md`

## 工作说明

### 修改代码时
1. **先读规范**: 操作前阅读 `docs/coding-standards.md`
2. **理解架构**: 参考 `docs/architecture.md` 了解模块关系
3. **确保安全**: 新 API 端点加 `@login_required`（除非是公开端点）；敏感端点加 `@rate_limit`
4. **数据溯源**: 新数据源结果须携带 `source` / `source_url` / `fetched_at` / `confidence`

### 前端修改
- 唯一文件: `templates/index.html` + `static/js/app.js` + `static/css/style.css`
- Markdown 渲染: `formatMarkdown()` 函数
- 快捷按钮: `appendFollowUpButtons()` 函数

### 后端修改
- `services.py` → `call_synscale()` 封装 LLM API 调用（多提供商故障切换）
- `services.py` → `run_agent()` 管理 Agent 循环（最多 3 轮，`MAX_ITERATIONS=3`）
- `agents.py` → `detect_intents()` 多意图检测 + `get_task_agents()` 任务拆解 + `get_agent_tools()` 工具子集分配
- `tools.py` → `TOOL_DESCRIPTIONS` (API schema) + `TOOL_FUNCTIONS` (实现映射)
- 认证: 所有敏感端点用 `@login_required`，读 `g.user_email`（不用 request body 的 user_email）

### 邮件发送流程（重要）
```
Agent 生成 draft → POST /api/email/draft（存草稿，不发送）
用户前端确认 → POST /api/email/draft/<id>/send（需 idempotency_key 防重复）
服务端校验 → mailer.send_email_smtp() 真实发送
```
**默认不应由 Agent 自动发送邮件。** 旧接口 `/api/email/smtp_send` 已弃用。

### 添加新工具
1. `tools.py` → 添加 `TOOL_DESCRIPTIONS` 中的 schema
2. `tools.py` → 实现工具函数（返回 JSON 字符串）
3. `tools.py` → 注册到 `TOOL_FUNCTIONS` 字典
4. `prompts.py` → 在 `SYSTEM_PROMPT` 中说明工具用途
5. `data_sources.py` → 如需新数据源（用 `enrich_result()` 加溯源字段）

### 添加新认证端点
1. 蓝图中导入 `from auth_middleware import login_required`
2. 添加 `@login_required` 装饰器
3. 读取 `g.user_email`（不再从 request body 取 user_email）
4. 写操作考虑加 `@rate_limit`

### 调试
```bash
# 测试 API（带 JWT token）
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@trademaster.com","password":"demo2024"}' | python -c "import sys,json; print(json.load(sys.stdin)['token'])")

curl -X POST http://127.0.0.1:5000/api/contacts/list \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN"

# 查看日志
type trademaster.log

# 运行测试
pytest tests/ -v --ignore=tests/test_e2e.py
```

### 完成任务后
1. 更新 `devlog/{date}.md` 记录完成事项
2. 运行 `pytest tests/ --ignore=tests/test_e2e.py` 确保 101 个测试通过
3. 如有未完成事项，写入待办列表

## 约束条件
- API 超时 60 秒，工具迭代最多 **3 轮** (`MAX_ITERATIONS=3`)
- 会话消息保存到 **SQLite**（最多 50 条/会话），重启不丢失
- 回答精简 150 字以内，开发信 100 字以内
- 前端单文件，不引入构建工具
- `.env`、`server.log`、`trademaster.log`、`trademaster.db` 不提交 Git
- **SECRET_KEY 必填** — 启动时缺失会报错退出
- 所有外部 API URL 必须 `https://`
- 买家/公司信息须携带 `source` / `source_url` / `fetched_at` / `confidence`
- Agent 生成邮件草稿 ≠ 发送；用户确认后才真正发出

## 当前版本
v2.1.0 (2026-08-07)
— JWT 认证、CORS 白名单、SMTP 密码加密、两阶段邮件确认、全端点限流、数据溯源、安全测试