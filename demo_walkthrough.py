# -*- coding: utf-8 -*-
"""
TradeMaster 演示链路脚本

用法:
    python demo_walkthrough.py [--url http://127.0.0.1:5000]

前提:
    TradeMaster 服务已启动 (python app.py)
    Demo 账号已初始化（首次启动自动创建 demo@trademaster.com / demo2024）

演示流程:
    1. 注册/登录 Demo 账号
    2. 搜索蓝牙耳机买家 → 展示来源和置信度
    3. 分析某公司详情
    4. 生成开发信 → 预览草稿（不发送）
    5. 查询汇率
    6. 查询展会知识
    7. 展示数据源故障时的降级提示
"""

import sys
import json
import time
import argparse
import requests

# ============================================================
# 配置
# ============================================================
DEMO_EMAIL = "demo@trademaster.com"
DEMO_PASSWORD = "demo2024"
BASE_URL = "http://127.0.0.1:5000"


def api_post(path, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.post(f"{BASE_URL}{path}", json=data, headers=headers, timeout=30)
    return resp.json() if resp.ok else {"error": resp.status_code, "body": resp.text}


def api_get(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=10)
    return resp.json() if resp.ok else {"error": resp.status_code}


def section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def step(n, title, description=""):
    print(f"\n--- 步骤 {n}: {title} ---")
    if description:
        print(f"  {description}")


# ============================================================
# 演示步骤
# ============================================================
def step1_login():
    """注册 / 登录 Demo 账号"""
    section("步骤 1: 登录 Demo 账号")
    resp = api_post("/api/login", {"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    if "token" in resp:
        print(f"✅ 登录成功")
        print(f"   用户: {resp.get('user', {}).get('email', '?')}")
        print(f"   公司: {resp.get('user', {}).get('company', '?')}")
        print(f"   产品: {resp.get('user', {}).get('product', '?')}")
        print(f"   JWT Token: {resp['token'][:40]}...")
        return resp["token"]
    else:
        print(f"❌ 登录失败: {resp}")
        # 尝试注册
        print("   尝试注册 Demo 账号...")
        resp = api_post("/api/register", {
            "email": DEMO_EMAIL, "password": DEMO_PASSWORD,
            "phone": "13800138001", "company": "深圳声海科技",
            "product": "bluetooth earphone", "identity": "seller",
        })
        if "token" in resp:
            print(f"✅ 注册并登录成功")
            return resp["token"]
        print(f"❌ 注册也失败了: {resp}")
        return None


def step2_search_buyers(token):
    """搜索蓝牙耳机买家"""
    section("步骤 2: 搜索蓝牙耳机买家")
    resp = api_post("/api/chat", {
        "message": "搜索德国蓝牙耳机进口商",
        "user_email": DEMO_EMAIL,
    })
    reply = resp.get("reply", "")
    tool_calls = resp.get("tool_calls", [])

    # 查找 search_buyers 工具调用结果
    for tc in tool_calls:
        if tc["tool"] == "search_buyers":
            result = tc.get("result", {})
            if isinstance(result, str):
                try: result = json.loads(result)
                except: pass
            if isinstance(result, dict):
                buyers = result.get("structured_results", [])
                print(f"✅ 找到 {len(buyers)} 条结构化结果")
                print(f"   搜索词: {result.get('search_terms_used', [])}")
                print(f"   数据获取时间: {result.get('fetched_at', 'N/A')}")
                if buyers:
                    b = buyers[0]
                    print(f"   第一条: {b.get('company_name', '?')}")
                    print(f"   数据来源: {b.get('data_source', '?')}")
                    # 检查溯源字段
                    if "source" in b or "confidence" in b:
                        print(f"   溯源字段: source={b.get('source', '?')}, "
                              f"confidence={b.get('confidence', '?')}")
    print(f"   Agent 回复前 200 字: {reply[:200]}...")


def step3_analyze_company(token):
    """分析公司详情"""
    section("步骤 3: 分析公司详情")
    resp = api_post("/api/chat", {
        "message": "分析 sennheiser.com 这家公司",
        "user_email": DEMO_EMAIL,
    })
    tool_calls = resp.get("tool_calls", [])
    for tc in tool_calls:
        if tc["tool"] == "analyze_company":
            result = tc.get("result", {})
            if isinstance(result, str):
                try: result = json.loads(result)
                except: pass
            if isinstance(result, dict):
                print(f"✅ 公司分析完成")
                print(f"   数据来源: {result.get('source', '?')}")
                info = result.get("company_info", {})
                print(f"   公司名: {info.get('company_name', '?')}")
                if "source" in info:
                    print(f"   溯源: source={info.get('source', '?')}, "
                          f"confidence={info.get('confidence', '?')}")


def step4_draft_email(token):
    """生成开发信草稿（不发送）"""
    section("步骤 4: 生成开发信 → 预览草稿（不发送）")
    # 方式 1: 通过 Agent 生成
    resp = api_post("/api/chat", {
        "message": "给 info@sennheiser.com 写一封蓝牙耳机开发信",
        "user_email": DEMO_EMAIL,
    })
    reply = resp.get("reply", "")
    print(f"   Agent 回复（前 300 字）:\n{reply[:300]}...")

    # 方式 2: 直接创建草稿（新两阶段流程）
    print("\n   📝 使用新的两阶段邮件流程:")
    draft_resp = api_post("/api/email/draft", {
        "to_email": "info@sennheiser.com",
        "subject": "Bluetooth Earphone Supply - Shenzhen SoundTech",
        "body": "Dear Sennheiser team,\n\nWe are a Shenzhen-based...",
        "to_name": "Sennheiser Procurement",
    }, token=token)
    if draft_resp.get("success"):
        print(f"   ✅ 草稿创建成功, draft_id={draft_resp.get('draft_id', '?')[:12]}...")
        print(f"   预览: {draft_resp.get('preview', {}).get('subject', '?')}")
        print(f"   提示: {draft_resp.get('message', '?')}")
    else:
        print(f"   ⚠️ 草稿创建: {draft_resp}")


def step5_exchange_rate(token):
    """查询汇率"""
    section("步骤 5: 查询汇率")
    resp = api_post("/api/chat", {
        "message": "美元兑人民币汇率是多少？",
        "user_email": DEMO_EMAIL,
    })
    tool_calls = resp.get("tool_calls", [])
    for tc in tool_calls:
        if tc["tool"] == "query_exchange_rate":
            result = tc.get("result", {})
            if isinstance(result, str):
                try: result = json.loads(result)
                except: pass
            if isinstance(result, dict):
                print(f"✅ 汇率查询完成")
                print(f"   数据来源: {result.get('source', '?')}")
                print(f"   置信度: {result.get('confidence', '?')}")
                print(f"   获取时间: {result.get('fetched_at', '?')}")
    print(f"   Agent 回复: {resp.get('reply', '')[:200]}...")


def step6_trade_knowledge(token):
    """查询展会知识"""
    section("步骤 6: 查询展会知识")
    resp = api_post("/api/chat", {
        "message": "查询蓝牙耳机相关的展会和认证要求",
        "user_email": DEMO_EMAIL,
    })
    tool_calls = resp.get("tool_calls", [])
    found = False
    for tc in tool_calls:
        if tc["tool"] == "search_trade_knowledge":
            result = tc.get("result", {})
            if isinstance(result, str):
                try: result = json.loads(result)
                except: pass
            print(f"✅ 知识检索完成")
            if isinstance(result, dict):
                print(f"   匹配展会: {len(result.get('tradeshows', []))} 条")
                print(f"   匹配认证: {len(result.get('certifications', []))} 条")
            found = True
    if found:
        print(f"   Agent 回复前 150 字: {resp.get('reply', '')[:150]}...")


def step7_health_and_source_status(token):
    """检查数据源状态"""
    section("步骤 7: 数据源状态 + 健康检查")
    resp = api_get("/api/health")
    if "checks" in resp:
        checks = resp["checks"]
        print(f"✅ 服务状态: {resp.get('status', '?')}")
        print(f"   数据库: {checks.get('database', '?')}")
        if "data_sources" in checks:
            ds = checks["data_sources"]
            print(f"   数据源:")
            for name, status in ds.items():
                icon = "✅" if status == "ok" else "⚠️"
                print(f"     {icon} {name}: {status}")
        if "llm_api" in checks:
            print(f"   LLM 提供商: {checks['llm_api']['providers']} 个")


def main():
    parser = argparse.ArgumentParser(description="TradeMaster 演示链路")
    parser.add_argument("--url", default=BASE_URL, help=f"服务地址（默认: {BASE_URL}）")
    args = parser.parse_args()
    global BASE_URL
    BASE_URL = args.url.rstrip("/")

    print("=" * 60)
    print("  TradeMaster 外贸通 — 演示链路")
    print(f"  服务: {BASE_URL}")
    print("=" * 60)

    # 步骤 1: 登录
    token = step1_login()
    if not token:
        print("\n❌ 无法登录，请确保服务已启动且 Demo 账号已初始化")
        print("   启动: python app.py")
        sys.exit(1)

    # 步骤 2-7
    try:
        step2_search_buyers(token)
    except Exception as e:
        print(f"⚠️ 步骤 2 失败: {e}")

    try:
        step3_analyze_company(token)
    except Exception as e:
        print(f"⚠️ 步骤 3 失败: {e}")

    try:
        step4_draft_email(token)
    except Exception as e:
        print(f"⚠️ 步骤 4 失败: {e}")

    try:
        step5_exchange_rate(token)
    except Exception as e:
        print(f"⚠️ 步骤 5 失败: {e}")

    try:
        step6_trade_knowledge(token)
    except Exception as e:
        print(f"⚠️ 步骤 6 失败: {e}")

    try:
        step7_health_and_source_status(token)
    except Exception as e:
        print(f"⚠️ 步骤 7 失败: {e}")

    print(f"\n{'=' * 60}")
    print(f"  演示完成！")
    print(f"  完整流程: 登录 → 搜索买家 → 分析公司 → 草稿邮件 → 汇率 → 知识检索 → 健康检查")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
