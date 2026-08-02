# 开发流程与执行步骤

## 每日开发流程

### 1. 开始工作前
- [ ] 拉取最新代码 (`git pull`)
- [ ] 检查 `.env` 配置是否正确
- [ ] 查看 `devlog/` 中昨日的待办事项
- [ ] 确认今日开发目标

### 2. 开发过程中
- [ ] 每个功能在独立分支开发
- [ ] 修改代码前先理解现有逻辑
- [ ] 遵循 `docs/coding-standards.md` 编码规范
- [ ] 复杂功能先写方案再编码
- [ ] 每次改动后验证功能是否正常

### 3. 提交代码前
- [ ] 运行 `python app.py` 确保无语法错误
- [ ] 测试 API 接口是否正常 (`curl http://127.0.0.1:5000/api/chat`)
- [ ] 检查前端渲染是否正常
- [ ] 提交信息遵循规范格式
- [ ] 更新 `devlog/` 记录今日完成事项

### 4. 每日收工前
- [ ] 更新 `devlog/{date}.md` 日志
- [ ] 标记未完成事项为待办
- [ ] 提交当日代码 (`git add . && git commit`)
- [ ] 推送到远程仓库 (`git push`)

## 环境配置

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
编辑 `.env` 文件：
```
SYNSCALE_API_KEY=your_api_key_here
SYNSCALE_MODEL_NAME=deepseek-v4-pro
```

### 启动开发服务器
```bash
python app.py
# 访问 http://127.0.0.1:5000
```

### 运行 API 测试
```bash
python test_api.py
```

## 项目文件结构
```
SW3_agent_trade/
├── app.py              # Flask 应用主入口 + Agent 逻辑
├── prompts.py          # 系统提示词
├── tools.py            # 工具定义与实现
├── data_sources.py     # 模拟数据源
├── main.py             # 独立测试脚本
├── test_api.py         # API 测试脚本
├── requirements.txt    # Python 依赖
├── .env                # 环境变量（不提交）
├── README.md           # 项目说明
├── CLAUDE.md           # AI 开发指南
├── templates/
│   └── index.html      # 前端单文件应用
├── docs/
│   ├── requirements.md          # 项目需求
│   ├── architecture.md          # 技术架构
│   ├── coding-standards.md      # 编码规范
│   └── development-workflow.md  # 开发流程（本文件）
└── devlog/
    └── YYYY-MM-DD.md  # 每日开发日志
```

## 常见开发任务

### 添加新工具
1. 在 `tools.py` 的 `TOOL_DESCRIPTIONS` 添加工具 schema
2. 在 `tools.py` 实现工具函数
3. 在 `TOOL_FUNCTIONS` 字典注册
4. 在 `prompts.py` 的 `SYSTEM_PROMPT` 中添加工具说明
5. 如果需要新数据，在 `data_sources.py` 添加
6. 更新 `docs/requirements.md`

### 修改前端UI
1. 编辑 `templates/index.html` 中的 `<style>` 或 `<script>`
2. 刷新浏览器即可看到效果（Flask debug 模式自动重载）

### 调试 API
1. 使用 `curl` 直接测试：
   ```bash
   curl -X POST http://127.0.0.1:5000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "你好", "session_id": "default"}'
   ```
2. 检查 `server.log` 中的错误信息

## 注意事项
- `.env` 和 `server.log` 不提交到 Git
- 保持依赖精简，避免引入重型框架
- 前端保持单文件，不引入构建工具
- API Key 过期或不可用时应给出明确提示