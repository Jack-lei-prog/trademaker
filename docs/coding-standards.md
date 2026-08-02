# 编码规范

## Python 编码规范

### 命名约定
- 文件名: `snake_case.py`（如 `data_sources.py`、`prompts.py`）
- 函数名: `snake_case`（如 `run_agent`、`call_synscale`）
- 常量: `UPPER_CASE`（如 `SYSTEM_PROMPT`、`MAX_ITERATIONS`）
- 变量: `snake_case`（如 `tool_calls_log`、`assistant_content`）

### 代码结构
- 每个模块顶部添加文档字符串说明用途
- 导入顺序：标准库 → 第三方库 → 项目模块
- 函数间空2行，类间空2行
- 行宽不超过120字符

### 错误处理
- API调用必须使用 try/except 包裹
- 工具函数返回 JSON 字符串，包含 success 字段
- 前端错误需返回友好中文提示

### 配置管理
- 所有敏感配置（API Key、URL）存储在 `.env` 文件
- 通过 `os.getenv()` 读取，不硬编码
- `.env` 加入 `.gitignore`

### 日志
- 使用 `print` 输出关键步骤日志
- 错误信息需包含足够的上下文

## 前端编码规范

### HTML/CSS
- 内联样式统一在 `<style>` 标签中定义
- 使用 CSS 变量管理主题色（规划中，当前使用硬编码渐变值）
- 响应式设计通过 `@media (max-width: 768px)` 断点实现

### JavaScript
- 使用 `var` 声明变量（兼容性考虑）
- 异步请求使用 `async/await` + `try/catch`
- DOM 操作集中管理，避免全局状态污染
- 函数命名: `camelCase`（如 `addMessage`、`formatMarkdown`）

### Markdown 渲染
- 段落之间用 `\n\n` 分隔
- 行内换行用 `<br>` 标签
- 处理顺序：HTML转义 → 代码块提取 → 表格提取 → 段落分割 → 内联格式
- 渲染后必须清理空白元素

## Git 规范

### 分支管理
- `main` — 生产分支，保持可部署状态
- `dev` — 开发分支
- `feature/xxx` — 功能分支
- `fix/xxx` — 修复分支

### 提交信息格式
```
<type>: <subject>

[可选 body]
```

类型:
- `feat`: 新功能
- `fix`: 修复
- `refactor`: 重构
- `style`: 样式调整
- `docs`: 文档更新
- `chore`: 杂项

### 示例
```
feat: 添加后续操作按钮到所有回复
fix: 修复段落末尾换行导致的空白区间
docs: 添加项目技术架构文档