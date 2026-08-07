# TradeMaster / 外贸通 - Intelligent Foreign Trade Assistant

基于大语言模型的智能外贸业务助理，12 个专业工具 + 6 个协作 Agent + RAG 知识库。

## Features

| 分类 | 功能 | 工具名 | 数据源 |
|------|------|--------|--------|
| 买家搜索 | 全球买家/进口商搜索 | `search_buyers` | Wikidata + OpenCorporates + LLM |
| 公司分析 | 公司注册信息查询 | `analyze_company` | OpenCorporates API |
| 邮件撰写 | B2B 开发信生成 | `draft_email` | LLM (Kimi/DeepSeek) |
| 邮件发送 | SMTP 邮件发送 + 追踪 | `send_email` | QQ邮箱 / Gmail SMTP |
| 汇率查询 | 160+ 货币实时汇率 | `query_exchange_rate` | open.er-api.com |
| 商品描述 | 电商文案生成 | `generate_product_desc` | LLM |
| 客服回复 | 智能客服回复起草 | `draft_customer_reply` | LLM |
| 销售分析 | 日销售简报 | `analyze_daily_sales` | LLM + 规则 |
| 营销广告 | 广告语生成 | `write_marketing_slogan` | LLM |
| 邮件状态 | 已发送邮件跟进检查 | `check_email_status` | 本地 DB |
| 询盘处理 | 客户询盘分类+回复+跟进 | `process_inquiry` | LLM + 规则 |
| 知识检索 | 展会/认证/术语 RAG 检索 | `search_trade_knowledge` | TF-IDF 知识库 |

## Architecture

```
Flask App (app.py)
  |-- config.py         集中配置 (env vars, 启动校验)
  |-- auth_middleware.py JWT 认证 (login_required 装饰器)
  |-- security.py       限流 + 输入校验 (RateLimitStore 抽象)
  |-- logger.py         结构化日志 (含敏感数据遮蔽)
  |
  |-- blueprints/       API 路由层
  |     |-- auth_bp.py      注册/登录 (JWT 令牌)
  |     |-- chat_bp.py      AI 对话 (同步 + SSE 流式)
  |     |-- email_bp.py     邮件草稿/发送/追踪/SMTP 设置
  |     |-- inquiry_bp.py   询盘处理
  |     |-- evaluate_bp.py  GAN 双评价器
  |     |-- contact_bp.py   客户联系人管理
  |     |-- dashboard_bp.py 仪表盘 + 一键获客
  |     |-- doll_bp.py      心情玩偶
  |
  |-- services.py       Agent 循环 (多 API 故障切换)
  |-- tools.py          12 个 Function Calling 工具
  |-- data_sources.py   外部数据源 (Wikidata/OpenCorp/汇率)
  |-- agents.py         6 个协作 Agent + 意图路由
  |-- prompts.py        系统提示词
  |-- db.py             SQLite 连接池 + Session/KV/联系人
  |-- evaluator.py      GAN 双评价器 (启发式 + Kimi)
  |-- mailer.py         SMTP 邮件发送
  |-- smtp_config.py    SMTP 配置 (密码加密存储)
  |-- smtp_crypto.py    Fernet 密码加密
  |-- user_service.py   用户注册/登录 bcrypt
  |-- inquiry_engine.py 询盘处理引擎
  |-- email_tracker.py  邮件追踪像素
  |-- imap_sync.py      IMAP 收件箱同步
  |-- cache.py          缓存工具
  |
  |-- knowledge/         RAG 知识库
  |     |-- retriever.py    TF-IDF 检索器
  |     |-- tradeshows.py   50+ 展会数据库
  |     |-- demo.py          Demo 演示数据
  |
  |-- skills/            Agent 技能包
  |-- templates/         前端 (index.html)
  |-- static/            静态资源
  |-- tests/             85 单元测试 + 16 安全测试 (共101)
```

## Quick Start

### 1. Prerequisites
- Python 3.10+
- LLM API Key (DeepSeek 推荐，或 Kimi/Moonshot)

### 2. Install
```bash
pip install -r requirements.txt
```

### 3. Configure `.env`
```bash
cp .env.example .env
# 编辑 .env，填入:
#   SECRET_KEY=<运行 python -c "import secrets; print(secrets.token_hex(32))" 生成>
#   LLM_API_KEY=sk-your-api-key
#   LLM_API_URL=https://api.deepseek.com/v1/chat/completions
#   LLM_MODEL=deepseek-chat
```

### 4. Run
```bash
python app.py
# 访问 http://127.0.0.1:5000
```

### 5. Demo Account
登录页面使用：
- 邮箱：`demo@trademaster.com`
- 密码：`demo2024`

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/register | No | 用户注册 (返回 JWT) |
| POST | /api/login | No | 用户登录 (返回 JWT) |
| POST | /api/chat | No | AI 对话 |
| POST | /api/chat/stream | No | AI 对话 (SSE 流式) |
| POST | /api/clear | No | 清空会话 |
| GET | /api/health | No | 健康检查 |
| GET | /api/docs | No | API 文档 |
| GET | /api/demo/help | No | 演示指南 |
| GET | /api/email/open/<id> | No | 邮件追踪像素 |
| POST | /api/send_email | JWT | 生成邮件预览 |
| POST | /api/email/draft | JWT | 创建邮件草稿 |
| POST | /api/email/draft/<id>/send | JWT | 确认发送草稿 |
| POST | /api/email/smtp_send | JWT | SMTP 直接发送 |
| POST | /api/email/smtp_settings | JWT | 读写 SMTP 配置 |
| POST | /api/email/smtp_test | JWT | SMTP 连接测试 |
| POST | /api/email/sync | JWT | IMAP 收件箱同步 |
| POST | /api/emails/sent | JWT | 已发送邮件列表 |
| POST | /api/emails/pending | JWT | 待跟进邮件 |
| POST | /api/emails/status | JWT | 更新邮件状态 |
| POST | /api/email/stats | JWT | 邮件统计 |
| POST | /api/email/classify | JWT | 邮件意图分类 |
| POST | /api/contacts/* | JWT | 客户联系人 CRUD |
| POST | /api/dashboard | JWT | 仪表盘数据 |
| POST | /api/workflow/* | JWT | 工作流管理 |
| POST | /api/preferences | JWT | 用户偏好 |
| POST | /api/customer-acquisition | JWT | 一键获客 |
| POST | /api/inquiry/* | JWT | 询盘处理 |
| POST | /api/evaluate/* | JWT | 回答评价 |
| POST | /api/doll/* | No | 心情玩偶 |
| POST | /api/upload/manual | No | 上传产品手册 |
| POST | /api/upload/excel | No | 上传客户 Excel |

## Multi-Agent System

6 个专业 Agent 协作，自动识别用户意图并路由：

| Agent | 职责 | 工具 |
|-------|------|------|
| Buyer Agent | 全球买家搜索 | search_buyers, analyze_company, search_trade_knowledge |
| Email Agent | B2B 邮件撰写 | draft_email, send_email, draft_customer_reply |
| Trade Agent | 展会情报 | search_trade_knowledge, query_exchange_rate, marketing |
| Inquiry Agent | 询盘处理 | process_inquiry |
| Dashboard Agent | 数据分析 | analyze_daily_sales, check_email_status |
| Coordinator | 意图识别+路由 | 全部工具 |

## Data Sources

| Source | Type | Confidence | Update |
|--------|------|-----------|--------|
| Wikidata | 公司实体 | 80% | Real-time API |
| OpenCorporates | 公司注册 | 85% | Real-time API |
| open.er-api.com | 汇率 | 95% | Daily |
| LLM (Kimi/DeepSeek) | 公司推荐/文案 | 50-70% | On-demand |
| 本地知识库 | 展会/认证/术语 | 90% | Static |

所有数据源返回均携带 `source`、`source_url`、`fetched_at`、`confidence` 溯源字段。
数据源故障时自动降级并在结果中标注。

## Security

- JWT 令牌认证 (HS256, 7天过期)
- bcrypt 密码哈希
- SMTP 密码 Fernet 加密存储
- 全端点频率限制
- CORS 显式白名单
- 安全响应头 (CSP, X-Frame-Options, X-Content-Type-Options)
- 敏感数据日志遮蔽
- 邮件幂等键防重复发送
- 两阶段邮件确认 (草稿 -> 用户确认 -> 发送)

## Testing

```bash
# 单元测试
python -m pytest tests/ -v

# 仅安全测试
python -m pytest tests/test_security.py -v
```

测试覆盖：用户系统、数据库 CRUD、工具函数、评价器、询盘引擎、认证绕过、越权访问、重复发送、限流、密码加密。

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| SECRET_KEY | **Yes** | - | Flask + JWT 密钥 |
| LLM_API_KEY | **Yes** | - | 主 LLM API Key |
| LLM_API_URL | No | moonshot.cn | LLM API 地址 |
| LLM_MODEL | No | kimi-k2.7-code | LLM 模型名 |
| CORS_ORIGINS | No | localhost | CORS 白名单 |
| FLASK_DEBUG | No | 0 | 调试模式 |
| SMTP_EMAIL | No | - | QQ邮箱地址 |
| SMTP_PASSWORD | No | - | QQ邮箱授权码 |
| JWT_EXPIRY_HOURS | No | 168 | JWT 过期时间 |

## Demo Walkthrough

可复现演示脚本，覆盖完整外贸链路 + 安全验证：

```bash
# 1. 启动 TradeMaster
python app.py

# 2. 运行演示走查（另一个终端）
python demo_walkthrough.py
```

演示内容：
1. 登录 Demo 账号（获取 JWT Token）
2. AI 搜索买家（展示数据来源、置信度、获取时间）
3. 公司分析（展示溯源字段）
4. 生成开发信草稿（两阶段流程：预览确认后才发送）
5. 实时汇率查询
6. 知识库检索（展会 + 认证）
7. 数据源健康状态检查（含故障降级提示）

## Deployment

```bash
gunicorn wsgi:app -w 2 -b 0.0.0.0:5000
```

支持 Render 一键部署 (render.yaml)。

## License

MIT License
