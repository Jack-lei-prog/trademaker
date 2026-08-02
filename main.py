"""
外贸业务助理 Agent 主程序
基于 ReAct 模式的智能外贸助手，通过调用工具完成客户搜索、公司分析、开发信撰写和汇率查询
"""

import os
import sys
import json
import requests
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 修复 Windows cmd 中文/emoji 编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 导入自定义模块
from prompts import SYSTEM_PROMPT
from tools import TOOL_FUNCTIONS, TOOL_DESCRIPTIONS

# 加载环境变量（从 .env 文件）
load_dotenv()

# SynScale API 配置
SYNSCALE_API_KEY = os.getenv("SYNSCALE_API_KEY")
SYNSCALE_API_URL = "http://synscale.onesyn.ai/v1/chat/completions"
MODEL_NAME = "qwen3.7-max"

# Agent 配置
MAX_ITERATIONS = 5  # 最大循环次数，避免死循环


def call_synscale(messages: List[Dict[str, Any]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    调用 SynScale API（兼容 OpenAI 格式）
    
    参数:
        messages: 消息列表，包含系统消息、用户消息和助手消息
        tools: 可用工具列表（可选）
    
    返回:
        API 响应的 JSON 字典
    
    异常:
        如果 API 调用失败，返回包含错误信息的字典
    """
    # 检查 API Key 是否配置
    if not SYNSCALE_API_KEY:
        return {
            "error": True,
            "message": "未配置 SYNSCALE_API_KEY，请在 .env 文件中设置"
        }
    
    # 构建请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SYNSCALE_API_KEY}"
    }
    
    # 构建请求体
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 800
    }
    
    # 如果提供了工具列表，添加到请求中
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    
    try:
        # 发送 POST 请求
        response = requests.post(
            SYNSCALE_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        # 检查 HTTP 状态码
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": True,
                "message": f"API 请求失败，状态码: {response.status_code}",
                "details": response.text
            }
    
    except requests.exceptions.Timeout:
        return {
            "error": True,
            "message": "API 请求超时，请稍后重试"
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": f"网络请求错误: {str(e)}"
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"未知错误: {str(e)}"
        }


def execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """
    执行指定的工具函数
    
    参数:
        tool_name: 工具名称
        tool_args: 工具参数字典
    
    返回:
        工具执行结果字符串
    """
    # 检查工具是否存在
    if tool_name not in TOOL_FUNCTIONS:
        return json.dumps({
            "error": True,
            "message": f"未知工具: {tool_name}",
            "available_tools": list(TOOL_FUNCTIONS.keys())
        }, ensure_ascii=False)
    
    try:
        # 调用对应的工具函数
        tool_func = TOOL_FUNCTIONS[tool_name]
        result = tool_func(**tool_args)
        return result
    
    except TypeError as e:
        # 参数类型错误
        return json.dumps({
            "error": True,
            "message": f"工具参数错误: {str(e)}",
            "tool": tool_name,
            "provided_args": tool_args
        }, ensure_ascii=False)
    
    except Exception as e:
        # 其他错误
        return json.dumps({
            "error": True,
            "message": f"工具执行失败: {str(e)}",
            "tool": tool_name
        }, ensure_ascii=False)


def print_welcome():
    """打印欢迎信息"""
    print("=" * 60)
    print("🌐 欢迎使用「外贸通」智能外贸业务助理")
    print("=" * 60)
    print()
    print("我可以帮您完成以下任务：")
    print("  🔍 搜索潜在买家")
    print("  📊 分析公司背景")
    print("  ✉️  撰写开发信")
    print("  💱 查询汇率信息")
    print("  📝 生成商品描述")
    print("  💬 起草客户回复")
    print("  📈 销售日报分析")
    print("  🎯 营销广告语生成")
    print()
    print("输入 'quit' 或 'exit' 退出程序")
    print("输入 'help' 查看使用示例")
    print("-" * 60)


def print_help():
    """打印帮助信息"""
    print()
    print("📖 使用示例：")
    print("-" * 40)
    print("1. 搜索买家：")
    print("   > 帮我搜索电子产品相关的买家")
    print()
    print("2. 分析公司：")
    print("   > 分析一下 techglobal.com 这家公司")
    print()
    print("3. 撰写开发信：")
    print("   > 给 TechGlobal 公司写一封开发信，推销我们的蓝牙耳机")
    print()
    print("4. 查询汇率：")
    print("   > 现在美元兑人民币的汇率是多少？")
    print()
    print("5. 商品描述生成：")
    print("   > 帮我为便携式迷你加湿器生成商品描述")
    print()
    print("6. 客户回复起草：")
    print("   > 客户问快递到哪了，帮我起草回复，订单已发货")
    print()
    print("7. 销售日报分析：")
    print("   > 分析今天的销售：保温杯20个，手机支架35个，数据线50个，总收入2800元")
    print()
    print("8. 营销广告语生成：")
    print("   > 为夏日防晒衣生成几条广告语")
    print()
    print("9. 组合任务：")
    print("   > 帮我找几个纺织品买家，分析他们的公司，然后写开发信")
    print("-" * 40)


def clean_response(text: str) -> str:
    """
    清理 AI 返回文本中的多余空行和空白字符
    
    参数:
        text: 原始文本
    
    返回:
        清理后的紧凑文本
    """
    if not text:
        return text
    
    lines = text.split("\n")
    cleaned_lines = []
    prev_blank = False
    
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            if not prev_blank:
                cleaned_lines.append("")
                prev_blank = True
        else:
            cleaned_lines.append(stripped)
            prev_blank = False
    
    while cleaned_lines and not cleaned_lines[0]:
        cleaned_lines.pop(0)
    while cleaned_lines and not cleaned_lines[-1]:
        cleaned_lines.pop()
    
    return "\n".join(cleaned_lines)


def run_agent(user_input: str) -> str:
    """
    运行 Agent 主循环，处理用户输入并返回最终回答
    
    参数:
        user_input: 用户输入的文本
    
    返回:
        Agent 的最终回答文本
    """
    # 初始化消息列表，以系统提示词作为第一条消息
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]
    
    # 记录当前迭代次数
    iteration = 0
    
    while iteration < MAX_ITERATIONS:
        iteration += 1
        print(f"\n[思考轮次 {iteration}/{MAX_ITERATIONS}]")
        
        # 调用 SynScale API
        print("正在调用 AI 模型...")
        response = call_synscale(messages, tools=TOOL_DESCRIPTIONS)
        
        # 检查是否有错误
        if "error" in response:
            error_msg = response.get("message", "未知错误")
            print(f"❌ 错误: {error_msg}")
            return f"抱歉，处理您的请求时遇到问题：{error_msg}"
        
        # 解析响应
        try:
            choices = response.get("choices", [])
            if not choices:
                return "抱歉，AI 模型未返回有效响应。"
            
            message = choices[0].get("message", {})
            assistant_content = message.get("content", "")
            tool_calls = message.get("tool_calls", [])
            
        except (KeyError, IndexError, TypeError) as e:
            print(f"❌ 解析响应失败: {e}")
            return "抱歉，无法解析 AI 模型的响应。"
        
        # 检查是否有工具调用
        if tool_calls:
            # 处理工具调用
            print(f"🔧 检测到 {len(tool_calls)} 个工具调用")
            
            # 将助手消息添加到历史记录
            messages.append({
                "role": "assistant",
                "content": assistant_content,
                "tool_calls": tool_calls
            })
            
            # 逐个执行工具调用
            for tool_call in tool_calls:
                try:
                    # 提取工具名称和参数
                    function_info = tool_call.get("function", {})
                    tool_name = function_info.get("name", "")
                    tool_args_str = function_info.get("arguments", "{}")
                    tool_call_id = tool_call.get("id", "")
                    
                    # 解析参数（JSON 字符串转字典）
                    try:
                        tool_args = json.loads(tool_args_str)
                    except json.JSONDecodeError:
                        tool_args = {}
                    
                    print(f"  📞 调用工具: {tool_name}")
                    print(f"     参数: {tool_args}")
                    
                    # 执行工具
                    tool_result = execute_tool(tool_name, tool_args)
                    
                    # 打印工具结果（截断显示）
                    result_preview = tool_result[:200] + "..." if len(tool_result) > 200 else tool_result
                    print(f"     结果: {result_preview}")
                    
                    # 将工具结果添加到消息历史
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": tool_result
                    })
                
                except Exception as e:
                    print(f"  ❌ 工具调用处理失败: {e}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", ""),
                        "content": json.dumps({
                            "error": True,
                            "message": f"工具调用处理失败: {str(e)}"
                        }, ensure_ascii=False)
                    })
        
        else:
            # 没有工具调用，说明模型已经准备好给出最终答案
            print("✅ 获得最终回答")
            return clean_response(assistant_content) if assistant_content else "（AI 未返回具体内容）"
    
    # 超过最大迭代次数
    print(f"\n⚠️ 已达到最大思考轮次 ({MAX_ITERATIONS})")
    return "抱歉，我思考了太多轮次仍未能得出结论。请尝试简化您的问题，或提供更多上下文信息。"


def main():
    """主函数：运行命令行交互界面"""
    # 打印欢迎信息
    print_welcome()
    
    # 检查 API Key 配置
    if not SYNSCALE_API_KEY:
        print("\n⚠️ 警告: 未检测到 SYNSCALE_API_KEY")
        print("请在 .env 文件中设置您的 API Key:")
        print("  SYNSCALE_API_KEY=your_api_key_here")
        print("\n程序将继续运行，但可能无法正常工作。\n")
    
    # 主循环
    while True:
        try:
            # 获取用户输入
            user_input = input("\n🧑 您: ").strip()
            
            # 检查退出命令
            if user_input.lower() in ["quit", "exit", "q", "退出"]:
                print("\n👋 感谢使用「外贸通」，祝您工作顺利！")
                break
            
            # 检查帮助命令
            if user_input.lower() in ["help", "h", "帮助"]:
                print_help()
                continue
            
            # 检查空输入
            if not user_input:
                continue
            
            # 运行 Agent
            print("\n🤖 外贸通: ", end="")
            response = run_agent(user_input)
            print(f"\n{response}")
        
        except KeyboardInterrupt:
            print("\n\n👋 程序已中断。感谢使用「外贸通」！")
            break
        
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            print("请检查您的输入或网络连接，然后重试。")


if __name__ == "__main__":
    main()