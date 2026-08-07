# TradeMaster 参赛演示指南

## 演示信息
- **演示账号**: demo@trademaster.com / demo2024
- **主营产品**: 蓝牙耳机 (Bluetooth Earphone)
- **演示时长**: 5分钟

---

## 演示脚本（5分钟）

### 0:00-0:30 开场 — 项目定位
```
"TradeMaster 外贸通 — AI外贸全流程智能体平台。

6 Agent 协作架构，覆盖外贸业务从找客户到成交的全链路。

打开 http://127.0.0.1:5000，登录演示账号。"
```

**展示点**:
- 登录页演示账号提示
- 玻璃拟态UI + 深色/浅色主题切换（点 🌓）

---

### 0:30-1:30 仪表盘 + 左侧展会面板
```
"登录后自动加载产品专属仪表盘：

左侧展会情报面板（点 📅 展开）：
- 📅 蓝牙耳机全球展会 (CES/IFA/HKTDC)
- 📋 出口认证要求 (CE/FCC/RoHS/BQB)
- 📊 市场洞察 (TWS市场$150B+)

主面板客户概览统计：预置3个示例客户（不同状态）"
```

**展示点**:
- 点左侧 📅 按钮 → 展开展会面板
- 折叠/展开各区域
- 右侧仪表盘客户统计

---

### 1:30-3:00 核心演示 — 搜索买家 + 开发信
```
"现在演示核心流程。输入'搜索德国蓝牙耳机进口商'。

Agent通过Function Calling自动调用 search_buyers Skill →
多数据源(Wikidata/OpenCorporates/LLM)协同搜索 →

返回5家德国买家清单，每家包含：
- 公司名/国家/网站
- 联系邮箱(标注 ⚠️未验证)
- 采购类型 + 推荐理由
- 大企业自动引导供应商注册(MediaMarkt → ceconomy.com/suppliers)

点击上下文按钮'给Thomann写开发信' →
Agent生成个性化英文开发信 →
内联编辑器展示，邮箱标注验证状态"
```

**展示点**:
- SSE流式输出实时可见
- 买家清单结构化展示
- 邮箱验证状态标注
- 大企业自动拦截并给供应商URL
- 开发信内联编辑器 + 发送选择

---

### 3:00-4:00 询盘处理 + 客户管理
```
"演示第二个场景：处理客户询盘。

粘贴一段模拟询盘：
'Dear supplier, we are TechGlobal Imports from UK,
interested in ANC bluetooth earphones.
Could you send FOB price for 3000 pcs?
Email: james@techglobal-imports.co.uk'

Agent自动完成5步闭环：
1. 提取客户信息 → TechGlobal, UK, james@...
2. 意图分类 → 真实采购(confidence: 0.72)
3. 公司背景调研 → OpenCorporates/Wikidata
4. 生成个性化英文回复
5. 加入48h跟进队列"
```

**展示点**:
- 客户画像提取
- 意图分类结果
- 自动生成的回复邮件
- 跟进队列记录

---

### 4:00-5:00 特色亮点 + 总结
```
"总结 TradeMaster 的核心优势：

1. 🛡️ 真实可落地 — 大企业邮箱自动拦截，推测邮箱标注验证状态
2. 📅 50+展会数据库 — 按产品智能匹配全球展会+参展策略
3. 🔄 多API故障切换 — 一个Key过期自动切到备用
4. 🧪 101个pytest — 覆盖核心模块
5. 🎨 玻璃拟态UI — 深浅色双主题，CSS变量驱动

技术栈：Python Flask + SQLite WAL + Kimi/DeepSeek双API
代码量：53文件，12000行"
```

---

## Skills 架构图

```
┌─────────────────────────────────────────┐
│           TradeMaster Agent             │
│     (Function Calling 调度中心)          │
├─────────────────────────────────────────┤
│  🔍 Buyer    │ ✉️ Email   │ 📅 Trade   │
│  Search      │ Draft      │ Intelligence│
│  Wikidata    │ B2B模板    │ 50+展会DB   │
│  OpenCorp    │ 企业拦截    │ 认证清单    │
│  LLM补充     │ 邮件发送    │ 市场洞察    │
├──────────────┼────────────┼─────────────┤
│  📬 Inquiry  │ 📊 Tracking│ 📋 CRM      │
│  5步闭环     │ 追踪像素    │ 7状态Pipeline│
│  意图分类    │ 退信检测    │ 多渠道记录   │
│  背景调研    │ 意图分类    │ 自动提醒     │
│  自动回复    │ SMTP直发    │ 逾期高亮     │
└─────────────────────────────────────────┘
```

## 项目文件结构

```
SW3_agent_trade/
├── app.py                  # Flask 主入口 (Blueprint注册)
├── services.py             # Agent循环 + 多API切换
├── prompts.py              # 系统提示词 (6 Skill定义)
├── tools.py                # 12个Function Calling工具
├── data_sources.py         # 多数据源 (Wikidata/OpenCorp/LLM)
├── db.py                   # SQLite WAL + 连接池 + KV存储
├── security.py             # 限流 + 输入校验
├── mailer.py               # SMTP发送 (QQ/Gmail)
├── email_tracker.py        # 追踪像素 + 意图分类
├── inquiry_engine.py       # 询盘5步闭环
├── evaluator.py            # GAN双评价 (启发式+Kimi)
├── cache.py                # TTL缓存 (线程安全)
├── user_service.py         # bcrypt用户认证
├── prompt_service.py       # 动态提示词构建
├── logger.py               # 结构化日志
│
├── skills/                 # 6 Agent协作模块
│   ├── buyer_search.py
│   ├── email_draft.py
│   ├── trade_intelligence.py
│   ├── inquiry_processing.py
│   ├── email_tracking.py
│   └── contact_management.py
│
├── knowledge/              # 知识库
│   ├── tradeshows.py       # 50+展会数据
│   └── demo.py             # 演示系统
│
├── blueprints/             # Flask Blueprint
│   ├── auth_bp.py          # 认证
│   ├── chat_bp.py          # 对话 (SSE流式)
│   ├── email_bp.py         # 邮件
│   ├── inquiry_bp.py       # 询盘
│   ├── evaluate_bp.py      # 评价
│   ├── contact_bp.py       # 客户管理
│   └── dashboard_bp.py     # 仪表盘
│
├── email_providers/        # 邮件后端
│   ├── local.py            # SQLite KV后端
│   └── gmail.py            # Gmail API后端
│
├── tests/                  # 测试 (58 passes)
├── static/                 # 前端
│   ├── css/style.css       # 玻璃拟态 + CSS变量
│   └── js/app.js           # 原生JS单文件
├── templates/index.html    # HTML模板
├── .env                    # API配置
└── DEMO.md                 # 本演示指南
```
