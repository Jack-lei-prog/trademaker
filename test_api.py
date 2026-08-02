import os
import requests
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量读取 API Key
api_key = os.getenv("SYNSCALE_API_KEY")

if not api_key:
    print("❌ 未找到 API Key，请检查 .env 文件")
    exit()

# 1. 先查询可用的模型列表（官方推荐第一步）[reference:2]
url_models = "http://synscale.onesyn.ai/v1/models"
headers = {"Authorization": f"Bearer {api_key}"}

try:
    response = requests.get(url_models, headers=headers)
    response.raise_for_status()
    data = response.json()
    print("✅ 可用模型列表：")
    model_id = None
    for model in data.get("data", []):
        model_id = model.get("id", "")
        print(f"  - {model_id}")
    
    # 使用第一个可用模型，如果未查到则使用默认模型
    if not model_id:
        model_id = data.get("data", [{}])[0].get("id", "deepseek-v4-flash") if data.get("data") else "deepseek-v4-flash"
except Exception as e:
    print(f"❌ 查询模型失败: {e}")
    exit()

# 2. 测试对话接口（使用 /chat/completions 兼容接口）[reference:3]
url_chat = "http://synscale.onesyn.ai/v1/chat/completions"
payload = {
    "model": model_id,  # 从上面的列表中选择一个
    "messages": [
        {"role": "user", "content": "你好，请用一句话介绍你自己"}
    ]
}

try:
    response = requests.post(url_chat, json=payload, headers=headers)
    response.raise_for_status()
    result = response.json()
    print("\n✅ 对话测试成功：")
    print(result['choices'][0]['message']['content'])
except Exception as e:
    print(f"❌ 对话测试失败: {e}")