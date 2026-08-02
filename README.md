# 🌐 外贸通 - 智能外贸业务助理 Agent

基于 ReAct 模式的智能外贸助手，能够调用工具完成客户搜索、公司分析、开发信撰写和汇率查询。

## 📋 项目功能

- **🔍 买家搜索**：根据关键词搜索潜在买家信息
- **📊 公司分析**：分析指定公司的背景信息
- **✉️ 开发信撰写**：根据客户信息和产品特点生成英文开发信
- **💱 汇率查询**：查询指定货币对人民币的汇率

## 📁 项目结构

```
SW3_agent_trade/
├── .env                # 环境变量配置（API Key）
├── prompts.py          # 系统提示词定义
├── tools.py            # 工具函数实现
├── main.py             # 命令行主程序入口
├── app.py              # Web 应用入口（Flask）
├── templates/          # HTML 模板目录
│   └── index.html      # Web 聊天界面
├── test_api.py         # API 连接测试脚本
├── requirements.txt    # Python 依赖包
└── README.md           # 项目说明文档
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+
- SynScale API Key（兼容 OpenAI 格式）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

在项目根目录创建或编辑 `.env` 文件，添加以下内容：

```
SYNSCALE_API_KEY=your_api_key_here
```

### 4. 测试 API 连接（可选）

```bash
python test_api.py
```

### 5. 运行程序

#### 方式一：命令行模式
```bash
python main.py
```

#### 方式二：Web 界面模式（推荐）
```bash
python app.py
```

然后在浏览器中访问：http://127.0.0.1:5000

## 💡 使用示例

启动程序后，您可以直接输入自然语言指令：

```
🧑 您: 帮我搜索电子产品相关的买家
🤖 外贸通: [返回搜索结果]

🧑 您: 分析一下 techglobal.com 这家公司
🤖 外贸通: [返回公司分析结果]

🧑 您: 给 TechGlobal 写一封开发信，推销蓝牙耳机
🤖 外贸通: [返回生成的开发信]

🧑 您: 美元兑人民币的汇率是多少？
🤖 外贸通: [返回汇率信息]
```

### 特殊命令

- `help` / `h` / `帮助` - 查看使用示例
- `quit` / `exit` / `q` / `退出` - 退出程序

## 🔧 技术说明

### ReAct 模式

本 Agent 采用 ReAct（Reasoning + Acting）模式：

1. **Thought（思考）**：分析用户问题，规划行动
2. **Action（行动）**：调用合适的工具（通过 OpenAI Function Calling）
3. **Observation（观察）**：分析工具返回结果
4. **循环**：重复以上步骤直到获得足够信息
5. **Final Answer**：给出最终回答

### 工具函数

所有工具函数位于 `tools.py`，当前使用模拟数据：

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| `search_buyers` | 买家搜索 | `keyword` |
| `analyze_company` | 公司分析 | `domain` |
| `draft_email` | 开发信撰写 | `company_info`, `product_highlight` |
| `query_exchange_rate` | 汇率查询 | `currency` |

### API 配置

- **API 端点**：`http://synscale.onesyn.ai/v1/chat/completions`
- **默认模型**：`qwen3.7-max`

### 扩展开发

如需接入真实 API，修改 `tools.py` 中对应的工具函数即可。

## 📝 注意事项

- 当前版本使用模拟数据，实际部署时需接入真实 API
- 开发信默认使用英文撰写
- 最大思考轮次为 5 次，避免死循环
- 请妥善保管您的 API Key，不要提交到公开仓库

## 📄 License

MIT License