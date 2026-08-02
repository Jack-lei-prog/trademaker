# CLAUDE.md - AI 开发指南

## 项目概述
**外贸通 (TradeMaster)** — 基于大语言模型的智能外贸业务助理 Web 应用。

## 快速启动
```bash
python app.py
# 访问 http://127.0.0.1:5000
```

## 标准文件路径

### 项目核心文件
| 文件 | 路径 | 说明 |
|------|------|------|
| 主应用 | `app.py` | Flask API + Agent 循环 |
| 提示词 | `prompts.py` | 系统提示词 SYSTEM_PROMPT |
| 工具定义 | `tools.py` | Function Calling 工具 schema 与实现 |
| 数据源 | `data_sources.py` | 模拟数据（买家、公司、汇率等） |
| 前端UI | `templates/index.html` | 单文件 HTML/CSS/JS |
| 环境配置 | `.env` | API Key 等敏感配置 |

### 文档目录 `docs/`
| 文件 | 路径 | 说明 |
|------|------|------|
| 项目需求 | `docs/requirements.md` | 功能需求、非功能需求、技术栈 |
| 技术架构 | `docs/architecture.md` | 系统架构图、模块职责、数据流 |
| 编码规范 | `docs/coding-standards.md` | Python/JS/HTML/CSS/Git 规范 |
| 开发流程 | `docs/development-workflow.md` | 每日流程、环境配置、常见任务 |

### 开发日志 `devlog/`
| 文件 | 路径 | 说明 |
|------|------|------|
| 每日日志 | `devlog/YYYY-MM-DD.md` | 每日完成事项 + 待办事项 |

## 工作说明

### 修改代码时
1. **先读规范**: 操作前阅读 `docs/coding-standards.md`
2. **理解架构**: 参考 `docs/architecture.md` 了解模块关系
3. **查看需求**: 确认改动是否符合 `docs/requirements.md`
4. **遵循流程**: 按 `docs/development-workflow.md` 执行

### 前端修改
- 唯一文件: `templates/index.html`
- 修改后刷新浏览器即可，Flask 自动重载
- Markdown 渲染逻辑在 `formatMarkdown()` 函数
- 快捷按钮在 `appendFollowUpButtons()` 函数

### 后端修改
- `app.py` 中的 `call_synscale()` 封装 LLM API 调用
- `run_agent()` 管理 Agent 循环（最多5轮）
- `TOOL_DESCRIPTIONS` 在 `tools.py`，与 API 通信
- 工具实现函数在 `tools.py` 中，映射在 `TOOL_FUNCTIONS`

### 添加新工具
1. `tools.py` → 添加 `TOOL_DESCRIPTIONS` 中的 schema
2. `tools.py` → 实现工具函数
3. `tools.py` → 注册到 `TOOL_FUNCTIONS` 字典
4. `prompts.py` → 在 `SYSTEM_PROMPT` 中说明工具用途
5. `data_sources.py` → 如需新数据在此添加

### 调试
```bash
# 测试 API
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "session_id": "default"}'

# 查看日志
type server.log
```

### 完成任务后
1. 更新 `devlog/{date}.md` 记录完成事项
2. 如有未完成事项，写入待办列表

## 约束条件
- API 超时 60 秒，工具迭代最多 5 轮
- 会话保留 15 条消息（内存存储，重启丢失）
- 回答精简 150 字以内，开发信 100 字以内
- 前端单文件，不引入构建工具
- `.env` 和 `server.log` 不提交 Git

## 当前版本
v1.0.0 (2026-08-01)