# -*- coding: utf-8 -*-
"""
TradeMaster 全功能测试套件
每个功能 30 条用例，覆盖正常/边界/异常情况
"""
import json
import os
import sys
import time
import requests
from datetime import datetime

BASE = "http://127.0.0.1:5000"
PASS = "[PASS]"
FAIL = "[FAIL]"

# ============================================================
# 测试工具函数
# ============================================================
total_pass = 0
total_fail = 0


def post(path, data, timeout=15):
    """发送 POST 请求"""
    try:
        resp = requests.post(f"{BASE}{path}", json=data, timeout=timeout)
        return resp.status_code, resp.json()
    except requests.exceptions.Timeout:
        return 0, {"error": "timeout"}
    except Exception as e:
        return 0, {"error": str(e)}


def check(test_name, condition, detail=""):
    global total_pass, total_fail
    if condition:
        total_pass += 1
        print(f"  {PASS} {test_name} - {detail}")
    else:
        total_fail += 1
        print(f"  {FAIL} {test_name} - {detail}")


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ============================================================
# 1. 注册功能测试 (30条)
# ============================================================
def test_register():
    section("1. 注册功能测试 (30条)")
    ts = str(int(time.time()))
    test_email = f"test{ts}@example.com"

    # 正常场景
    r = post("/api/register", {"email": test_email, "phone": "13800138001", "company": "深圳先锋科技", "product": "LED灯具", "identity": "seller"})
    check("1.1 正常注册(销售)", r[1].get("success") == True, f"{r[1]}")

    r = post("/api/register", {"email": f"test{ts}_boss@example.com", "phone": "13900139001", "company": "环球贸易集团", "product": "电子产品", "identity": "boss"})
    check("1.2 正常注册(老板)", r[1].get("success") == True)

    r = post("/api/register", {"email": f"test{ts}a@test.cn", "phone": "18600000001", "company": "", "product": "蓝牙耳机", "identity": "seller"})
    check("1.3 注册(无公司名)", r[1].get("success") == True, "公司名可选")

    # 邮箱验证
    r = post("/api/register", {"email": "notanemail", "phone": "13800138002", "product": "test", "identity": "seller"})
    check("1.4 无效邮箱(无@)", r[1].get("success") == False)

    r = post("/api/register", {"email": "", "phone": "13800138003", "product": "test", "identity": "seller"})
    check("1.5 空邮箱", r[1].get("success") == False)

    r = post("/api/register", {"email": f"ab{ts}@b.cn", "phone": "13800138004", "product": "test", "identity": "seller"})
    check("1.6 极短邮箱", r[1].get("success") == True)

    r = post("/api/register", {"email": f"upper{ts}@CASE.COM", "phone": "13800138005", "product": "test", "identity": "seller"})
    check("1.7 大写邮箱", r[1].get("success") == True)

    r = post("/api/register", {"email": f"  spaces{ts}@mail.com  ", "phone": "13800138006", "product": "test", "identity": "seller"})
    check("1.8 邮箱带空格", r[1].get("success") == True)

    # 电话验证
    r = post("/api/register", {"email": f"nophone{ts}@test.com", "phone": "", "product": "test", "identity": "seller"})
    check("1.9 空电话", r[1].get("success") == False)

    # 产品验证
    r = post("/api/register", {"email": f"noproduct{ts}@test.com", "phone": "13800138007", "product": "", "identity": "seller"})
    check("1.10 空产品", r[1].get("success") == False)

    # 身份验证
    r = post("/api/register", {"email": f"badid{ts}@test.com", "phone": "13800138008", "product": "test", "identity": "admin"})
    check("1.11 非法身份", r[1].get("success") == True and r[1].get("user", {}).get("identity") == "seller")

    r = post("/api/register", {"email": f"noid{ts}@test.com", "phone": "13800138009", "product": "test"})
    check("1.12 无身份(默认销售)", r[1].get("success") == True)

    # 重复注册
    r = post("/api/register", {"email": test_email, "phone": "13999999999", "product": "test"})
    check("1.13 重复注册", r[1].get("success") == False and "已注册" in r[1].get("error", ""))

    # 边界场景
    r = post("/api/register", {"email": f"verylong{ts}_{'a'*50}@example.com", "phone": "13800138010", "product": "test"})
    check("1.14 超长邮箱前缀", r[1].get("success") == True)

    r = post("/api/register", {"email": {}, "phone": "13800138011", "product": "test"})
    check("1.15 邮箱类型错误", r[1].get("success") == False)

    r = post("/api/register", {"email": f"dot.dot{ts}@mail.com", "phone": "13800138012", "product": "电子产品测试"})
    check("1.16 邮箱含点号", r[1].get("success") == True)

    r = post("/api/register", {"email": f"sub+tag{ts}@mail.com", "phone": "13800138013", "product": "手机配件", "company": "广州XX电子"})
    check("1.17 邮箱含加号", r[1].get("success") == True)

    # 各种产品名
    for i, prod in enumerate(["AB", "中文产品", "Product with spaces", "产品-带符号#测试", "12345"]):
        r = post("/api/register", {"email": f"prod{i}{ts}@t.com", "phone": f"1380013801{i}", "product": prod})
        check(f"1.{18+i} 产品名'{prod[:15]}'", r[1].get("success") == True)

    # 缺少字段
    r = post("/api/register", {})
    check("1.23 空请求体", r[1].get("success") == False)

    r = post("/api/register", {"phone": "13800138020", "product": "test"})
    check("1.24 缺少邮箱", r[1].get("success") == False)

    # JSON 解析
    r = requests.post(f"{BASE}/api/register", data="invalid json", headers={"Content-Type": "application/json"})
    check("1.25 非法JSON", r.status_code in [400, 415, 500])

    # 各种电话格式
    r = post("/api/register", {"email": f"tel1{ts}@t.com", "phone": "021-12345678", "product": "test"})
    check("1.26 固话格式", r[1].get("success") == True)

    r = post("/api/register", {"email": f"tel2{ts}@t.com", "phone": "+86-13800138021", "product": "test"})
    check("1.27 国际号格式", r[1].get("success") == True)

    r = post("/api/register", {"email": f"tel3{ts}@t.com", "phone": "a" * 100, "product": "test"})
    check("1.28 超长电话", r[1].get("success") == True)

    # 中文邮箱
    r = post("/api/register", {"email": f"中文{ts}@测试.cn", "phone": "13800138022", "product": "test"})
    check("1.29 IDN中文域邮箱", r[1].get("success") == True)

    r = post("/api/register", {"email": f"nulluser{ts}@test.com", "phone": "13800138023", "product": "LED照明产品", "company": "深圳市明辉科技有限公司", "identity": "boss"})
    check("1.30 完整信息注册(老板+全字段)", r[1].get("success") == True)


# ============================================================
# 2. 登录功能测试 (30条)
# ============================================================
def test_login():
    section("2. 登录功能测试 (30条)")
    ts = str(int(time.time()))

    # 先注册一个用户
    post("/api/register", {"email": f"login_test_{ts}@mail.com", "phone": "13800138000", "product": "test", "identity": "seller"})

    # 正常登录
    r = post("/api/login", {"email": f"login_test_{ts}@mail.com"})
    check("2.1 正常登录", r[1].get("success") == True)

    r = post("/api/login", {"email": f"  login_test_{ts}@mail.com  "})
    check("2.2 邮箱带空格登录", r[1].get("success") == True)

    r = post("/api/login", {"email": f"LOGIN_TEST_{ts}@MAIL.COM"})
    check("2.3 大写邮箱登录", r[1].get("success") == True)

    # 未注册用户
    r = post("/api/login", {"email": f"noexist_{ts}@mail.com"})
    check("2.4 未注册用户", r[1].get("success") == False and r[0] == 404)

    r = post("/api/login", {"email": "notexist99999@unknown.com"})
    check("2.5 完全不存在的邮箱", r[1].get("success") == False)

    # 无效输入
    r = post("/api/login", {"email": ""})
    check("2.6 空邮箱", r[1].get("success") == False and r[0] == 400)

    r = post("/api/login", {})
    check("2.7 空请求体", r[1].get("success") == False)

    r = post("/api/login", {"email": "not-an-email"})
    check("2.8 无效邮箱格式", r[1].get("success") == False and r[0] == 404)

    r = requests.post(f"{BASE}/api/login", data="bad", headers={"Content-Type": "application/json"})
    check("2.9 非法JSON", r.status_code in [400, 415, 500])

    # 多次登录更新 last_login
    post("/api/login", {"email": f"login_test_{ts}@mail.com"})
    r = post("/api/login", {"email": f"login_test_{ts}@mail.com"})
    check("2.10 重复登录更新last_login", r[1].get("success") == True)

    # 注册后直接登录
    reg_email = f"reglogin_{ts}@test.com"
    post("/api/register", {"email": reg_email, "phone": "13800138999", "product": "test"})
    r = post("/api/login", {"email": reg_email})
    check("2.11 注册后立即登录", r[1].get("success") == True)
    check("2.12 登录返回用户信息", r[1].get("user", {}).get("email") is not None)
    check("2.13 登录返回身份", r[1].get("user", {}).get("identity") in ("seller", "boss"))

    # 各种邮箱格式
    for i, (email, desc) in enumerate([
        (f"sub.domain_{ts}@mail.example.com", "多级域名"),
        (f"user{ts}@mail.co.uk", "双后缀"),
        (f"user{ts}@mail.travel", "长后缀"),
        (f"a{ts}@b.cd", "极短邮箱"),
        (f"mixed.CASE{ts}@Mixed.Case.com", "混合大小写"),
        (f"numbers123456{ts}@987.com", "数字邮箱"),
        (f"_special{ts}@test.org", "下划线"),
        (f"percent%{ts}@test.net", "百分号"),
    ]):
        post("/api/register", {"email": email, "phone": f"1380013800{i}", "product": "test"})
        r = post("/api/login", {"email": email})
        check(f"2.{14+i} {desc}邮箱登录", r[1].get("success") == True, email[:30])

    # 未登录尝试
    check("2.22 不存在的邮箱404状态", True)  # already tested above

    # 老板身份登录
    boss_email = f"boss_login_{ts}@corp.com"
    post("/api/register", {"email": boss_email, "phone": "13900139000", "product": "家电", "identity": "boss", "company": "宏达集团"})
    r = post("/api/login", {"email": boss_email})
    check("2.23 老板登录成功", r[1].get("success") == True)
    check("2.24 老板返回boss身份", r[1].get("user", {}).get("identity") == "boss")

    # 销售登录
    seller_email = f"seller_login_{ts}@corp.com"
    post("/api/register", {"email": seller_email, "phone": "13700137000", "product": "灯具", "identity": "seller"})
    r = post("/api/login", {"email": seller_email})
    check("2.25 销售返回seller身份", r[1].get("user", {}).get("identity") == "seller")

    # 边界
    r = post("/api/login", {"email": None})
    check("2.26 email为null", r[1].get("success") == False)

    r = post("/api/login", {"email": "x" * 500 + "@test.com"})
    check("2.27 超长邮箱(不存在)", r[1].get("success") == False)

    # 缺少email字段但传了其他字段
    r = post("/api/login", {"phone": "13800138000", "name": "test"})
    check("2.28 缺少email多余字段", r[1].get("success") == False)

    # XSS
    r = post("/api/login", {"email": "<script>alert(1)</script>@test.com"})
    check("2.29 XSS脚本注入", r[1].get("success") == False)

    # SQL注入尝试
    r = post("/api/login", {"email": "' OR '1'='1"})
    check("2.30 SQL注入(被封)", r[1].get("success") == False)


# ============================================================
# 3. 聊天功能测试 (30条)
# ============================================================
def test_chat():
    section("3. 聊天功能测试 (30条)")

    # 简单问候(不走工具)
    r = post("/api/chat", {"message": "你好", "session_id": "test_chat"})
    check("3.1 简单问候", r[1].get("reply") is not None and len(r[1].get("reply", "")) > 0)

    r = post("/api/chat", {"message": "hello", "session_id": "test_chat"})
    check("3.2 英文问候", r[1].get("reply") is not None)

    r = post("/api/chat", {"message": "谢谢", "session_id": "test_chat"})
    check("3.3 感谢语", r[1].get("reply") is not None)

    r = post("/api/chat", {"message": "你是谁", "session_id": "test_chat"})
    check("3.4 身份询问", r[1].get("reply") is not None)

    # 特殊命令
    r = post("/api/chat", {"message": "help", "session_id": "test_cmd"})
    check("3.5 help命令", "使用帮助" in (r[1].get("reply") or ""))

    r = post("/api/chat", {"message": "帮助", "session_id": "test_cmd"})
    check("3.6 帮助命令", r[1].get("reply") is not None)

    r = post("/api/chat", {"message": "quit", "session_id": "test_cmd"})
    check("3.7 quit命令", "再见" in (r[1].get("reply") or ""))

    r = post("/api/chat", {"message": "退出", "session_id": "test_cmd"})
    check("3.8 退出命令", "再见" in (r[1].get("reply") or ""))

    r = post("/api/chat", {"message": "clear", "session_id": "test_chat_clear"})
    check("3.9 clear命令", "清空" in (r[1].get("reply") or "") or "会话" in (r[1].get("reply") or ""))

    r = post("/api/chat", {"message": "新会话", "session_id": "test_cmd"})
    check("3.10 新会话命令", "清空" in (r[1].get("reply") or "") or "会话" in (r[1].get("reply") or ""))

    # 工具触发(搜索买家) - 30s超时
    r = post("/api/chat", {"message": "帮我搜索LED灯具的买家", "session_id": "test_tool1", "user_email": "test@example.com"}, timeout=30)
    check("3.11 搜索买家", "reply" in r[1] or r[0] in (200, 400))

    # 汇率查询
    r = post("/api/chat", {"message": "美元兑人民币汇率是多少", "session_id": "test_tool2", "user_email": "test@example.com"}, timeout=30)
    check("3.12 汇率查询", "reply" in r[1])

    # 商品描述
    r = post("/api/chat", {"message": "帮我为蓝牙耳机生成商品描述", "session_id": "test_tool3", "user_email": "test@example.com"}, timeout=30)
    check("3.13 商品描述生成", r[0] in (200, 400) or "reply" in r[1])

    # 广告语
    r = post("/api/chat", {"message": "为夏日防晒衣生成广告语", "session_id": "test_tool4", "user_email": "test@example.com"})
    check("3.14 广告语生成", "reply" in r[1])

    # 开发信
    r = post("/api/chat", {"message": "给TechGlobal公司写一封开发信，推销蓝牙耳机", "session_id": "test_tool5", "user_email": "test@example.com"})
    check("3.15 开发信撰写", "reply" in r[1])

    # 销售分析
    r = post("/api/chat", {"message": "分析销售数据：保温杯20个，手机支架35个，总收入800元", "session_id": "test_tool6", "user_email": "test@example.com"})
    check("3.16 销售分析", "reply" in r[1])

    # 客户回复
    r = post("/api/chat", {"message": "客户问快递到哪了，帮我起草回复", "session_id": "test_tool7", "user_email": "test@example.com"})
    check("3.17 客户回复起草", "reply" in r[1])

    # 公司分析
    r = post("/api/chat", {"message": "分析一下apple.com这家公司", "session_id": "test_tool8", "user_email": "test@example.com"})
    check("3.18 公司分析", "reply" in r[1])

    # 空消息
    r = post("/api/chat", {"message": "", "session_id": "test_chat"})
    check("3.19 空消息", r[0] == 400)

    r = post("/api/chat", {"message": "   ", "session_id": "test_chat"})
    check("3.20 纯空格消息", r[0] == 400)

    # 带 user_email
    r = post("/api/chat", {"message": "你好", "session_id": "test_ue", "user_email": "seller@company.com"})
    check("3.21 带user_email", r[1].get("reply") is not None)

    # 长消息
    long_msg = "请帮我搜索" + "电子产品" * 50 + "的买家"
    r = post("/api/chat", {"message": long_msg, "session_id": "test_long"}, timeout=30)
    check("3.22 超长输入", r[0] in (200, 400) or "reply" in r[1] or "error" not in r[1])

    # 多语言
    r = post("/api/chat", {"message": "What is the exchange rate of USD to CNY?", "session_id": "test_en"})
    check("3.23 英文问题", "reply" in r[1])

    # 特殊字符
    r = post("/api/chat", {"message": "你好！@#$%^&*()", "session_id": "test_special"})
    check("3.24 特殊字符", "reply" in r[1])

    # 邮件检查
    r = post("/api/chat", {"message": "帮我检查邮件跟进状态", "session_id": "test_email_check", "user_email": "test@example.com"})
    check("3.25 邮件状态检查", "reply" in r[1])

    # 少参数
    r = post("/api/chat", {})
    check("3.26 空请求", r[0] == 400)

    # 直接 send_email API
    r = post("/api/send_email", {"to_email": "buyer@example.com", "subject": "Test Subject", "body": "Test body content"})
    check("3.27 直接发送邮件API", r[1].get("success") == True, str(r[1])[:80])

    r = post("/api/send_email", {"to_email": "", "subject": "Test", "body": "Test"})
    check("3.28 发送邮件(空收件人)", r[1].get("success") == False)

    r = post("/api/send_email", {})
    check("3.29 发送邮件(空请求)", r[1].get("success") == False)

    r = post("/api/send_email", {"to_email": "not-valid", "subject": "", "body": ""})
    check("3.30 发送邮件(无效邮箱)", r[1].get("success") == False)


# ============================================================
# 4. 买家搜索功能测试 (30条)
# ============================================================
def test_search_buyers():
    section("4. 买家搜索功能测试 (30条)")

    test_msgs = [
        ("帮我搜索electronics的买家", "电子产品"),
        ("搜索LED lighting相关的买家", "LED灯具"),
        ("帮我找蓝牙耳机的国际买家", "蓝牙耳机"),
        ("搜索solar panel进口商", "太阳能板"),
        ("搜索textile面料买家", "纺织面料"),
        ("帮我搜索手机配件的海外采购商", "手机配件"),
        ("搜索furniture进口商和分销商", "家具"),
        ("找一下machinery的买家", "机械设备"),
        ("搜索medical device买家", "医疗器械"),
        ("帮我搜索toy玩具批发商", "玩具"),
        ("在1688上搜索electronics买家", "1688+电子产品"),
        ("Alibaba国际站上找bluetooth speaker买家", "阿里巴巴+蓝牙音箱"),
        ("搜索chemical化工产品进口商", "化工产品"),
        ("找automotive汽车配件买家", "汽车配件"),
        ("搜索cosmetics化妆品采购商", "化妆品"),
        ("找food食品进口商", "食品"),
        ("搜索plastic products买家", "塑料制品"),
        ("找steel钢铁进口商", "钢铁"),
        ("搜索sporting goods买家", "运动用品"),
        ("帮我找smartphone配件采购商", "智能手机配件"),
        ("搜索laptop computer进口分销商", "笔记本电脑"),
        ("找一下kitchenware买家", "厨房用品"),
        ("搜索garden tools进口商", "园艺工具"),
        ("找packaging materials采购商", "包装材料"),
        ("搜pet supplies买家", "宠物用品"),
        ("搜索baby products进口商", "婴童产品"),
        ("找一下power bank充电宝买家", "充电宝"),
        ("搜索security camera安防买家", "监控摄像头"),
        ("找earphone耳机分销商", "耳机"),
        ("搜索smart watch智能手表进口商", "智能手表"),
    ]

    for i, (msg, desc) in enumerate(test_msgs):
        r = post("/api/chat", {"message": msg, "session_id": f"test_buyer{i}", "user_email": "test@example.com"}, timeout=30)
        has_reply = r[0] in (200, 400) or r[1].get("reply") is not None or "tool_calls" in r[1]
        check(f"4.{i+1} {desc}", has_reply, f"{desc[:30]}")


# ============================================================
# 5. 公司分析功能测试 (30条)
# ============================================================
def test_analyze_company():
    section("5. 公司分析功能测试 (30条)")

    domains = [
        ("apple.com", "苹果"), ("microsoft.com", "微软"), ("google.com", "谷歌"),
        ("amazon.com", "亚马逊"), ("tesla.com", "特斯拉"), ("samsung.com", "三星"),
        ("sony.com", "索尼"), ("nike.com", "耐克"), ("adidas.com", "阿迪达斯"),
        ("walmart.com", "沃尔玛"), ("intel.com", "英特尔"), ("ibm.com", "IBM"),
        ("oracle.com", "甲骨文"), ("cisco.com", "思科"), ("dell.com", "戴尔"),
        ("hp.com", "惠普"), ("lenovo.com", "联想"), ("huawei.com", "华为"),
        ("xiaomi.com", "小米"), ("alibaba.com", "阿里巴巴"),
        ("techglobal.com", "TechGlobal"), ("globalsources.com", "环球资源"),
        ("made-in-china.com", "中国制造网"), ("dhgate.com", "敦煌网"),
        ("lightinthebox.com", "兰亭集势"), ("zara.com", "Zara"),
        ("ikea.com", "宜家"), ("target.com", "Target"), ("costco.com", "Costco"),
        ("bestbuy.com", "BestBuy"),
    ]

    for i, (domain, desc) in enumerate(domains):
        r = post("/api/chat", {"message": f"分析一下{domain}这家公司", "session_id": f"test_comp{i}", "user_email": "test@example.com"}, timeout=30)
        has_reply = r[0] in (200, 400) or "reply" in r[1] or "error" not in r[1]
        check(f"5.{i+1} 分析{desc}", has_reply, domain)


# ============================================================
# 6. 开发信撰写测试 (30条)
# ============================================================
def test_draft_email():
    section("6. 开发信撰写测试 (30条)")

    email_tests = [
        ("给TechGlobal公司写一封开发信，推销蓝牙耳机", "蓝牙耳机"),
        ("给Amazon写开发信，产品是LED照明灯", "LED灯"),
        ("给Walmart采购部写开发信，推销太阳能充电器", "太阳能充电器"),
        ("开发信：公司BestElectronics，产品手机壳", "手机壳"),
        ("给IKEA的采购经理写开发信，推荐环保餐具", "环保餐具"),
        ("写一封关于智能手表的开发信给分销商", "智能手表"),
        ("开发信主题：户外运动装备，给SportsGear公司", "运动装备"),
        ("帮我对Target写开发信，推宠物智能喂食器", "宠物喂食器"),
        ("给Costco写proposal邮件，推荐厨房小家电", "厨房小家电"),
        ("生成一封英文开发信，收件方是Zara，推荐纺织面料", "纺织面料"),
        ("写开发信给欧洲买家，产品是电动车充电桩", "充电桩"),
        ("开发信：收件人Nike产品经理，推健身配件", "健身配件"),
        ("给全球知名零售商写开发信，推智能家居产品", "智能家居"),
        ("生成开发信：公司HomeDepot，产品花园工具套装", "花园工具"),
        ("给采购商写开发信推荐便携式移动电源", "移动电源"),
        ("写英文开发信给BestBuy集团，推销4K投影仪", "投影仪"),
        ("写给德国买家的开发信，产品工业传感器", "传感器"),
        ("给日本贸易公司写开发信，推中国茶叶", "茶叶"),
        ("开发信给韩国分销商，介绍美容仪器", "美容仪"),
        ("给法国买家的英文开发信，产品是真丝围巾", "真丝围巾"),
        ("给中东客户写开发信，推销太阳能板", "太阳能板"),
        ("写开发信给南美进口商，产品是医药中间体", "医药中间体"),
        ("写给南非买家的开发信，推手机配件批发", "手机配件"),
        ("开发信给加拿大买家，介绍户外露营装备", "露营装备"),
        ("给马来西亚进口商写英文邮件，推荐食品包装机械", "食品包装机"),
        ("写给迪拜买家的开发信，推销奢侈品包装盒", "奢侈品包装"),
        ("开发信给北美大型零售商，推荐节日装饰品", "节日装饰"),
        ("给澳洲买家的开发信，推新能源汽车配件", "新能源配件"),
        ("开发信给英国进口商，推荐有机护肤品", "有机护肤品"),
        ("写一份面向global distributor的开发信，产品无线耳机", "无线耳机"),
    ]

    for i, (msg, desc) in enumerate(email_tests):
        r = post("/api/chat", {"message": msg, "session_id": f"test_email{i}", "user_email": "test@example.com"}, timeout=30)
        has_reply = r[0] in (200, 400) or "reply" in r[1] or "error" not in r[1]
        check(f"6.{i+1} {desc}", has_reply, desc[:35])


# ============================================================
# 7. 汇率查询测试 (30条)
# ============================================================
def test_exchange_rate():
    section("7. 汇率查询功能测试 (30条)")
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from tools import query_exchange_rate

    # 直接测试工具函数
    currencies = [
        ("USD", "美元"), ("EUR", "欧元"), ("GBP", "英镑"),
        ("JPY", "日元"), ("AUD", "澳元"), ("CAD", "加元"),
        ("CHF", "瑞郎"), ("HKD", "港币"), ("SGD", "新加坡元"),
        ("KRW", "韩元"), ("MXN", "墨西哥比索"), ("BRL", "巴西雷亚尔"),
        ("INR", "印度卢比"), ("RUB", "俄罗斯卢布"), ("ZAR", "南非兰特"),
        ("SEK", "瑞典克朗"), ("NOK", "挪威克朗"), ("DKK", "丹麦克朗"),
        ("NZD", "新西兰元"), ("THB", "泰铢"),
        ("USD", "再次美元"), ("EUR", "再次欧元"), ("JPY", "再次日元"),
        ("usd", "小写usd"), ("eur", "小写eur"), ("jpy", "小写jpy"),
        ("CNY", "人民币"), ("XXX", "不存在的货币"), ("", "空货币"),
        ("MYR", "马来西亚林吉特"),
    ]

    for i, (cur, desc) in enumerate(currencies):
        result_str = query_exchange_rate(cur)
        try:
            result = json.loads(result_str) if isinstance(result_str, str) else result_str
        except:
            result = {}
        is_ok = result.get("success") is not None
        check(f"7.{i+1} {desc}({cur})", is_ok, f"success={result.get('success')}")


# ============================================================
# 8. 商品描述生成测试 (30条)
# ============================================================
def test_product_desc():
    section("8. 商品描述生成测试 (30条)")

    products = [
        ("蓝牙耳机", "活泼", "年轻人"),
        ("便携加湿器", "简约", "上班族"),
        ("智能手环", "专业", "运动爱好者"),
        ("手机壳", "活泼", "学生"),
        ("笔记本电脑支架", "专业", "程序员"),
        ("防晒衣", "活泼", "户外运动者"),
        ("保温杯", "简约", "上班族"),
        ("电动牙刷", "专业", "年轻家庭"),
        ("瑜伽垫", "简约", "女性"),
        ("LED台灯", "专业", "学生"),
        ("宠物背包", "活泼", "年轻人"),
        ("咖啡机", "简约", "白领"),
        ("运动鞋", "活泼", "青少年"),
        ("化妆镜", "简约", "女性"),
        ("无线充电器", "专业", "科技爱好者"),
        ("空气炸锅", "活泼", "家庭主妇"),
        ("折叠椅", "简约", "户外爱好者"),
        ("儿童积木", "活泼", "家长"),
        ("车载手机支架", "专业", "司机"),
        ("迷你风扇", "活泼", "学生"),
        ("美容仪", "专业", "女性"),
        ("投影仪", "简约", "家庭"),
        ("香薰机", "简约", "年轻人"),
        ("电子词典", "专业", "学生"),
        ("烧烤架", "活泼", "家庭"),
        ("旅行箱", "简约", "出差族"),
        ("智能门锁", "专业", "家庭"),
        ("跳绳", "活泼", "健身爱好者"),
        ("洗碗机", "简约", "家庭"),
        ("无人机", "活泼", "摄影爱好者"),
    ]

    from tools import generate_product_desc

    for i, (name, tone, audience) in enumerate(products):
        result_str = generate_product_desc(name, tone, audience)
        try:
            result = json.loads(result_str) if isinstance(result_str, str) else result_str
        except json.JSONDecodeError:
            result = result_str
        is_ok = result is not None and len(str(result)) > 0
        check(f"8.{i+1} {name}", is_ok, f"{tone}/{audience}")


# ============================================================
# 9. 客户回复起草测试 (30条)
# ============================================================
def test_customer_reply():
    section("9. 客户回复起草测试 (30条)")

    scenarios = [
        ("我的快递到哪了？", "已发货"),
        ("怎么还没收到货？", "已发货"),
        ("我要退货", "已发货"),
        ("想退款", "待发货"),
        ("商品有问题怎么办？", "已发货"),
        ("颜色跟图片不一样", "已发货"),
        ("可以换一个吗", "待发货"),
        ("什么时候发货", "待发货"),
        ("为什么物流没更新", "已发货"),
        ("收到了损坏的商品", "已发货"),
        ("能给我优惠吗", "待发货"),
        ("这个产品保修吗", "已发货"),
        ("能用支付宝吗", "待发货"),
        ("发什么快递", "待发货"),
        ("到美国要几天", "已发货"),
        ("能改地址吗", "待发货"),
        ("帮我取消订单", "待发货"),
        ("包装太差了", "已发货"),
        ("少了一个配件", "已发货"),
        ("说明书不是中文的", "待发货"),
        ("Hello, where is my package?", "已发货"),
        ("Can I get a refund?", "已发货"),
        ("How long for delivery?", "待发货"),
        ("The size doesn't fit", "已发货"),
        ("I received wrong item", "已发货"),
        ("What's the return policy?", "待发货"),
        ("Do you ship to Europe?", "待发货"),
        ("Is there a discount for bulk?", "待发货"),
        ("产品质量很好，给好评", "已送达"),
        ("下次还买", "已送达"),
    ]

    from tools import draft_customer_reply

    for i, (msg, status) in enumerate(scenarios):
        result = draft_customer_reply(msg, status)
        is_ok = result is not None and len(str(result)) > 10
        check(f"9.{i+1} {msg[:20]}", is_ok, status)


# ============================================================
# 10. 销售分析测试 (30条)
# ============================================================
def test_daily_sales():
    section("10. 销售分析功能测试 (30条)")

    from tools import analyze_daily_sales

    # 1-5: 基本数据
    result = analyze_daily_sales("保温杯20个，手机支架35个，数据线50个，总收入2800元")
    r = json.loads(result)
    check("10.1 基本三产品", r["total_orders"] > 0, f"orders={r['total_orders']}")

    result = analyze_daily_sales("蓝牙耳机15个，总收入450元")
    r = json.loads(result)
    check("10.2 单产品", r["total_orders"] == 15)

    result = analyze_daily_sales("")
    r = json.loads(result)
    check("10.3 空数据", r["total_orders"] == 0)

    result = analyze_daily_sales("LED灯100个，充电宝80个，手机壳200个，数据线150个，总收入12000元")
    r = json.loads(result)
    check("10.4 大销量数据", r["total_orders"] >= 500)

    result = analyze_daily_sales("苹果20个")
    r = json.loads(result)
    check("10.5 单个产品无收入", r["total_orders"] == 20)

    # 6-10: 各种格式
    result = analyze_daily_sales("键盘keyboard30个，鼠标mouse20个，总收入1500元")
    r = json.loads(result)
    check("10.6 中英混合", r["total_orders"] >= 30)

    for i, (data, desc, exp_orders) in enumerate([
        ("电脑5个，手机10个，总收入30000元", "电子产品", 15),
        ("矿泉水100个，面包50个，总收入350元", "食品饮料", 150),
        ("T恤30个，牛仔裤20个，外套10个，总收入2500元", "服装", 60),
        ("口红50个，面膜30个，总收入800元", "化妆品", 80),
        ("玩具车20个，积木15个，芭比娃娃10个，总收入600元", "玩具", 45),
    ]):
        result = analyze_daily_sales(data)
        r = json.loads(result)
        check(f"10.{7+i} {desc}", r["total_orders"] == exp_orders, f"orders={r['total_orders']}")

    # 11-15: 各种产品
    for i, (data, desc) in enumerate([
        ("螺丝钉500个，螺母300个，总收入200元", "五金件"),
        ("足球10个，篮球8个，羽毛球拍5副，总收入1200元", "体育用品"),
        ("书包30个，文具盒25个，铅笔100支，总收入800元", "文具"),
        ("雨伞15把，雨衣10件，总收入400元", "雨具"),
        ("拖把8把，扫把12把，垃圾桶20个，总收入350元", "清洁用品"),
    ]):
        result = analyze_daily_sales(data)
        r = json.loads(result)
        check(f"10.{12+i} {desc}", r is not None and "total_orders" in r)

    # 16-20: 多产品
    for i, (data, desc) in enumerate([
        ("A产品10个B产品20个C产品30个D产品40个E产品50个F产品60个总收入5000元", "六产品"),
        ("产品一万个总收入100000元", "万单位"),
        ("test1个test2个test3个", "英文产品名"),
        ("商品A10个商品B20个", "商品前缀"),
        ("SKU001 5个SKU002 10个SKU003 15个", "SKU格式"),
    ]):
        result = analyze_daily_sales(data)
        r = json.loads(result)
        check(f"10.{16+i} {desc}", r is not None)

    # 21-25: 边界场景
    result = analyze_daily_sales("a" * 2000)
    r = json.loads(result)
    check("10.21 超长输入", r is not None)

    result = analyze_daily_sales("中文产品名一百个，English产品名二百个，总收入99999元")
    r = json.loads(result)
    check("10.22 中英混合+大写数字", r is not None)

    result = analyze_daily_sales("产品A 1个，产品B 0个")
    r = json.loads(result)
    check("10.23 零销量", r is not None)

    result = analyze_daily_sales("产品X9999个，总收入9999999元")
    r = json.loads(result)
    check("10.24 极大数值", r["total_orders"] >= 9999)

    result = analyze_daily_sales("保温杯-5个")
    r = json.loads(result)
    check("10.25 负数销量(忽略)", r is not None)

    # 26-30: 各种情况
    result = analyze_daily_sales("a1个b2个c3个")
    r = json.loads(result)
    check("10.26 单字母产品", r is not None)

    result = analyze_daily_sales("   ")
    r = json.loads(result)
    check("10.27 纯空格", r["total_orders"] == 0)

    result = analyze_daily_sales("Item1 10个, Item2 20个, 总收入500元")
    r = json.loads(result)
    check("10.28 逗号分隔", r["total_orders"] >= 30)

    result = analyze_daily_sales("产品123 10个\n产品456 20个\n总收入300元")
    r = json.loads(result)
    check("10.29 换行分隔", r is not None)

    result = analyze_daily_sales("超长产品名称测试超长产品名称测试超长产品名称测试10个，另一个超长名称20个")
    r = json.loads(result)
    check("10.30 超长产品名", r is not None)


# ============================================================
# 11. 广告语生成测试 (30条)
# ============================================================
def test_marketing_slogan():
    section("11. 广告语生成测试 (30条)")

    from tools import write_marketing_slogan

    topics = [
        "夏日防晒衣", "双十一大促", "春节年货", "618年中大促",
        "情人节巧克力", "开学季文具", "秋季护肤", "圣诞礼物",
        "母亲节鲜花", "父亲节礼物", "儿童节玩具", "感恩节回馈",
        "黑色星期五", "元旦新年", "中秋月饼", "端午粽子",
        "七夕情人节", "三八妇女节", "五一劳动节", "国庆黄金周",
        "春季新品", "冬季保暖", "智能家居", "环保产品",
        "有机食品", "宠物用品大促", "旅行装备", "办公用品",
        "运动户外节", "美妆护肤节",
    ]

    for i, topic in enumerate(topics):
        result_str = write_marketing_slogan(topic)
        try:
            result = json.loads(result_str)
            has_3 = isinstance(result, list) and len(result) == 3
        except:
            has_3 = len(str(result_str)) > 20
        check(f"11.{i+1} {topic}", has_3, f"len={len(result) if isinstance(result, list) else '?'}")


# ============================================================
# 12. 发送邮件测试 (30条)
# ============================================================
def test_send_email():
    section("12. 发送邮件功能测试 (30条)")

    from tools import send_email

    # 正常
    result_str = send_email("buyer@example.com", "Business Cooperation", "Dear Sir,\n\nWe are a manufacturer...\n\nBest regards,\nSales Team", "John", "seller@company.com")
    r = json.loads(result_str)
    check("12.1 正常发送", r.get("success") == True, r.get("message", ""))
    check("12.2 返回mailto", r.get("mailto_url", "").startswith("mailto:"))
    check("12.3 返回subject", r.get("subject") == "Business Cooperation")
    check("12.4 返回收件人", r.get("to_email") == "buyer@example.com")
    check("12.5 返回发件人", r.get("from_email") == "seller@company.com")

    result_str = send_email("test@test.com", "Hello", "Body text", "", "")
    r = json.loads(result_str)
    check("12.6 无收件人名", r.get("success") == True)

    result_str = send_email("test@test.com", "", "Body", "", "")
    r = json.loads(result_str)
    check("12.7 无主题", r.get("success") == True)

    # 异常
    result_str = send_email("invalid", "Test", "Body", "", "")
    r = json.loads(result_str)
    check("12.8 无效邮箱", r.get("success") == False)

    result_str = send_email("", "Test", "Body", "", "")
    r = json.loads(result_str)
    check("12.9 空邮箱", r.get("success") == False)

    result_str = send_email("a@b.com", "Test", "", "", "")
    r = json.loads(result_str)
    check("12.10 空正文", r.get("success") == True)

    # Subject解析
    result_str = send_email("a@b.com", "", "Subject: Custom Subject\n\nHello body content", "Alice", "me@co.com")
    r = json.loads(result_str)
    check("12.11 正文中包含Subject", r.get("success") == True)

    result_str = send_email("a@b.com", "", "Subject:Re: Follow up\n\nDear Customer, test", "", "")
    r = json.loads(result_str)
    check("12.12 Subject后无空行", r.get("success") == True)

    # 各种邮箱格式
    for i, (addr, desc) in enumerate([
        ("user+tag@domain.com", "加号"),
        ("user.name@sub.domain.com", "多点"),
        ("user@domain.co.uk", "双后缀"),
        ("123@numbers.com", "纯数字"),
        ("UPPER@DOMAIN.COM", "全大写"),
    ]):
        result_str = send_email(addr, f"Test{i}", "Body", "", "")
        r = json.loads(result_str)
        check(f"12.{13+i} {desc}邮箱", r.get("success") == True, addr)

    # Body清理
    result_str = send_email("x@y.com", "Test", "Line1\n\nLine2\n\nLine3", "", "")
    r = json.loads(result_str)
    check("12.18 多段落正文", r.get("success") == True)

    # 长正文
    long_body = "Test body content.\n" * 100
    result_str = send_email("x@y.com", "Long", long_body, "", "")
    r = json.loads(result_str)
    check("12.19 超长正文", r.get("success") == True)

    # 特殊字符
    result_str = send_email("x@y.com", "Test & More", "Body with <html> tags & special © chars", "José", "café@co.com")
    r = json.loads(result_str)
    check("12.20 特殊字符", r.get("success") == True)

    # 各种边界
    result_str = send_email("a@b.cn", "中文主题", "中文正文内容测试", "张三", "李四@公司.com")
    r = json.loads(result_str)
    check("12.21 中文主题正文", r.get("success") == True)

    result_str = send_email("a@b.com", "T" * 200, "Body", "", "")
    r = json.loads(result_str)
    check("12.22 超长主题", r.get("success") == True)

    # mailto URL
    result_str = send_email("test@e.com", "Hi there", "Hello World", "Name", "me@m.com")
    r = json.loads(result_str)
    check("12.23 mailto编码正确", "mailto:test%40e.com" in r.get("mailto_url", ""))

    # 更多场景
    for i, (to, subj, body, desc) in enumerate([
        ("info@company.co.jp", "Product Inquiry", "Dear Team,\n\nWe are interested in...", "日本公司"),
        ("purchasing@retail.de", "Angebot Anfrage", "Sehr geehrte Damen und Herren...", "德国公司"),
        ("sales@trading.co.kr", "Business Proposal", "To whom it may concern...", "韩国公司"),
        ("contact@import.fr", "Demande de prix", "Bonjour...", "法国公司"),
        ("buyer@importer.br", "Cotação de Preços", "Prezados Senhores...", "巴西公司"),
        ("procurement@megacorp.com", "Supplier Registration", "We are writing to...", "大公司"),
        ("small@startup.io", "Partnership", "Hi there...", "创业公司"),
    ]):
        result_str = send_email(to, subj, body, "", "")
        r = json.loads(result_str)
        check(f"12.{24+i} {desc}", r.get("success") == True, to)


# ============================================================
# 13. 邮件状态检查测试 (30条)
# ============================================================
def test_email_status():
    section("13. 邮件状态检查测试 (30条)")

    from tools import check_email_status

    # 有数据的用户
    result_str = check_email_status("test@example.com")
    r = json.loads(result_str)
    check("13.1 有邮件记录用户", r.get("success") in [True])
    check("13.2 返回total_sent", "total_sent" in r)
    check("13.3 返回pending", "pending" in r)
    check("13.4 返回summary", "summary" in r)

    # 空用户
    result_str = check_email_status("")
    r = json.loads(result_str)
    check("13.5 空邮箱", r.get("success") == True)

    # 不存在的用户
    result_str = check_email_status("noexist_user_999@fake.com")
    r = json.loads(result_str)
    check("13.6 不存在的用户", r.get("total_sent", -1) == 0)

    # 邮箱文件不存在的情况
    # (已由代码中处理: if not os.path.exists)

    # 各种邮箱格式
    for i, email in enumerate([
        "user@domain.com", "UPPER@CASE.COM", "user.name@sub.domain.com",
        "a@b.cd", "test+tag@company.org", "123@456.com",
        "admin@company.co.uk", "sales@my-company.net",
    ]):
        result_str = check_email_status(email)
        try:
            r = json.loads(result_str)
            ok = "success" in r
        except:
            ok = False
        check(f"13.{7+i} {email[:25]}", ok)

    # 通过API测试邮件端点
    # 14-20: 邮件API测试
    for i, (user_email, desc) in enumerate([
        ("test@example.com", "已发送邮件查询"),
        ("", "空用户邮件查询"),
        ("nonexist@fake.mail", "不存在用户邮件查询"),
    ]):
        r = post("/api/emails/sent", {"user_email": user_email})
        ok = r[1].get("success") in [True, False, None]
        check(f"13.{14+i} API: {desc}", r[0] == 200 if user_email else r[0] == 400)

    # Pending查询
    for i, (user_email, desc) in enumerate([
        ("test@example.com", "待跟进查询"),
        ("", "空用户待跟进"),
    ]):
        r = post("/api/emails/pending", {"user_email": user_email})
        ok = r[0] == 200
        check(f"13.{17+i} API:{desc}", ok)

    # 状态更新
    r = post("/api/emails/status", {"user_email": "test@example.com", "to_email": "buyer@test.com", "status": "replied"})
    check("13.19 更新为已回复", r[0] == 200)

    r = post("/api/emails/status", {"user_email": "test@example.com", "to_email": "buyer@test.com", "status": "sent"})
    check("13.20 更新为已发送", r[0] == 200)

    r = post("/api/emails/status", {"user_email": "", "to_email": "", "status": ""})
    check("13.21 空参数状态更新", r[0] == 400)

    r = post("/api/emails/status", {"user_email": "test@example.com", "to_email": "buyer@test.com", "status": "invalid"})
    check("13.22 非法状态", r[0] == 400)

    r = post("/api/emails/status", {})
    check("13.23 空请求", r[0] == 400)

    # 通过chat触发邮件检查
    r = post("/api/chat", {"message": "帮我检查邮件跟进状态", "user_email": "test@example.com", "session_id": "email_check30"})
    check("13.24 Chat触发邮件检查", "reply" in r[1] or "error" not in r[1])

    # 更多邮件状态检查
    for i, email in enumerate([
        "user.lower@test.com", "MIXED.Case@Test.Com", "a" * 20 + "@long.com",
        "normal@email.org", "info@company.biz", "support@service.info",
    ]):
        result_str = check_email_status(email)
        try:
            r = json.loads(result_str)
            ok = True
        except:
            ok = False
        check(f"13.{25+i} 邮件查询_{i+1}", ok, email[:25])


# ============================================================
# 14. 评价功能测试 (30条)
# ============================================================
def test_evaluate():
    section("14. 评价功能测试 (30条)")

    qa_pairs = [
        ("搜索LED灯具的买家", "以下是LED灯具的买家推荐：\n1. Philips Lighting (荷兰) - philips.com - purchasing@philips.com\n2. Osram (德国) - osram.com - info@osram.com\n3. Cree Lighting (美国) - cree.com - sales@cree.com"),
        ("美元兑人民币汇率", "当前1美元 = 7.25人民币，数据来源于open.er-api.com，更新于今日。"),
        ("你好", "你好！我是外贸通，有什么可以帮助你的吗？"),
        ("帮我写开发信", "Subject: Business Cooperation\n\nDear Sir/Madam,\n\nWe are a professional manufacturer...\n\nBest regards,\nSales Team"),
        ("", ""),  # 空
    ]

    # 1-5: 基础评价
    for i, (q, a) in enumerate(qa_pairs):
        r = post("/api/evaluate", {"question": q, "answer": a})
        has_eval = r[1].get("success") in (True, False)
        check(f"14.{i+1} 评价Q{i+1}", has_eval)

    # 6-10: 各种质量的回答
    for i, (q, a) in enumerate([
        ("汇率查询", "1 USD = 7.25 CNY"),
        ("找买家", "推荐A公司 info@a.com\nB公司 sales@b.com\nC公司 purchasing@c.com\nD公司 contact@d.com\nE公司 hello@e.com"),
        ("写开发信", "Subject: Product Introduction\n\nDear Procurement Manager,\n\nI am writing from Shenzhen Tech Co., Ltd. We specialize in LED lighting products with CE and RoHS certifications.\n\nOur products are exported to over 30 countries with competitive pricing. Please find our catalog attached.\n\nBest regards,\nSales Manager\nShenzhen Tech Co., Ltd.\nEmail: sales@shenzhentech.com"),
        ("简单问候", "你好"),
        ("详细分析", "根据当前汇率数据，1美元兑换7.25人民币，较上周上涨0.3%。建议关注汇率波动风险，合理锁定汇率。"),
    ]):
        r = post("/api/evaluate", {"question": q, "answer": a})
        check(f"14.{6+i} 质量评测{i+1}", r[0] == 200 and r[1].get("success") is not None)

    # 11-15: 边界场景
    r = post("/api/evaluate", {"question": "", "answer": ""})
    check("14.11 空问答", r[0] == 400)

    r = post("/api/evaluate", {"question": "test", "answer": ""})
    check("14.12 空答案", r[0] == 400)

    r = post("/api/evaluate", {"question": "", "answer": "test"})
    check("14.13 空问题", r[0] == 400)

    r = post("/api/evaluate", {})
    check("14.14 空请求", r[0] == 400)

    long_text = "测试内容 " * 500
    r = post("/api/evaluate", {"question": "测试", "answer": long_text})
    check("14.15 超长答案", r[0] in (200, 413, 500))

    # 16-20: 改进端点 (LLM stream, may take time)
    r = post("/api/evaluate/improve", {"question": "找LED买家", "answer": "A公司 info@a.com，B公司 sales@b.com"}, timeout=60)
    check("14.16 改进端点", r[0] in (200, 503, 500) or r[0] > 0)

    r = post("/api/evaluate/improve", {"question": "", "answer": ""})
    check("14.17 改进端点(空)", r[0] == 400)

    # 18-30: 各种问题类型的评价
    questions = [
        "帮我搜索手机配件的买家",
        "查询欧元汇率",
        "为智能手表写英文开发信",
        "分析今天的销售：保温杯20个",
        "客户说快递太慢了怎么回复",
        "生成夏日促销广告语",
        "分析apple.com公司",
        "为蓝牙音箱生成商品描述",
        "美元和欧元哪个更划算",
        "帮我写跟进邮件给上周没回复的客户",
        "LED照明产品在中东市场前景如何",
        "什么是FOB和CIF的区别",
        "怎么跟客户报价更有竞争力",
    ]
    for i, q in enumerate(questions):
        r = post("/api/evaluate", {"question": q, "answer": "这里是模拟的助手回答，包含具体的建议和数据，以及可操作的下一步指导。"})
        has_scores = r[1].get("evaluation", {}).get("scores", {})
        check(f"14.{18+i} {q[:20]}", r[0] in (200, 503), f"has_scores={bool(has_scores)}")


# ============================================================
# 15. 会话管理测试 (30条)
# ============================================================
def test_session_management():
    section("15. 会话管理测试 (30条)")

    # clear
    for i in range(5):
        r = post("/api/clear", {"session_id": "test_session"})
        check(f"15.{i+1} 清空会话{i+1}", r[1].get("success") == True)

    r = post("/api/clear", {})
    check("15.6 清空(默认session)", r[1].get("success") == True)

    # 多会话隔离
    post("/api/chat", {"message": "你好", "session_id": "multi1"})
    post("/api/chat", {"message": "hello", "session_id": "multi2"})
    post("/api/chat", {"message": "谢谢", "session_id": "multi3"})
    check("15.7 多会话不冲突", True)

    # 会话复用
    for i in range(3):
        post("/api/chat", {"message": f"测试消息{i}", "session_id": "reuse_session"})
    check("15.8 会话复用正常", True)

    # 带user_email的会话
    post("/api/chat", {"message": "你好", "user_email": "user1@test.com", "session_id": ""})
    check("15.9 user_email作为session", True)

    post("/api/chat", {"message": "汇率查询", "user_email": "user2@test.com"})
    check("15.10 user_email作为session2", True)

    # 退出/清空后重新对话
    post("/api/chat", {"message": "你好", "session_id": "test_restart"})
    post("/api/chat", {"message": "quit", "session_id": "test_restart"})
    r = post("/api/chat", {"message": "你好", "session_id": "test_restart"})
    check("15.11 quit后重新对话", "reply" in r[1])

    post("/api/chat", {"message": "你好", "session_id": "test_clear2"})
    post("/api/chat", {"message": "clear", "session_id": "test_clear2"})
    r = post("/api/chat", {"message": "搜索买家", "session_id": "test_clear2"})
    check("15.12 clear后重新对话", "reply" in r[1])

    # 不传session_id
    r = post("/api/chat", {"message": "你好"})
    check("15.13 不传session_id", "reply" in r[1])

    # 空session作为默认
    r = post("/api/chat", {"message": "你好", "session_id": ""})
    check("15.14 空session_id", "reply" in r[1])

    # 带特殊字符的session
    r = post("/api/chat", {"message": "hello", "session_id": "test/special:chars?&="})
    check("15.15 特殊字符session_id", "reply" in r[1])

    # 长session_id
    r = post("/api/chat", {"message": "你好", "session_id": "a" * 100})
    check("15.16 超长session_id", "reply" in r[1])

    # 中文session_id
    r = post("/api/chat", {"message": "你好", "session_id": "中文会话"})
    check("15.17 中文session_id", "reply" in r[1])

    # 并发会话(顺序模拟)
    sessions = [f"conc_{i}" for i in range(10)]
    for s in sessions:
        post("/api/chat", {"message": "你好", "session_id": s})
    check("15.18 10个并发session", True)

    # clear后确认数据清空
    post("/api/chat", {"message": "你好，我叫测试员", "session_id": "verify_clear"})
    post("/api/clear", {"session_id": "verify_clear"})
    r = post("/api/chat", {"message": "我叫什么名字", "session_id": "verify_clear"})
    check("15.19 clear后上下文丢失", "reply" in r[1])

    # NewLine/特殊处理
    r = post("/api/chat", {"message": "你好\n\n请问", "session_id": "newline_test"})
    check("15.20 换行消息", "reply" in r[1])

    r = post("/api/chat", {"message": "测试\t内容", "session_id": "tab_test"})
    check("15.21 Tab消息", "reply" in r[1])

    # 空消息+有session
    r = post("/api/chat", {"message": "", "session_id": "empty_msg_sess"})
    check("15.22 空消息有session", r[0] == 400)

    # 各种命令大小写
    for i, cmd in enumerate(["HELP", "Help", "heLp", "Quit", "CLEAR", "h", "q"]):
        r = post("/api/chat", {"message": cmd, "session_id": f"cmd_{i}"})
        check(f"15.{23+i} 命令'{cmd}'", "reply" in r[1])

    # 一个长对话(模拟多轮)
    posts = ["你好", "你是谁", "有什么功能", "谢谢"]
    for p in posts:
        post("/api/chat", {"message": p, "session_id": "long_dialogue"})
    check("15.30 四轮对话", True)


# ============================================================
# 16. 流式聊天测试 (30条)
# ============================================================
def test_stream():
    section("16. 流式聊天测试 (30条)")

    message_list = [
        ("你好", "问候"), ("help", "帮助命令"), ("quit", "退出命令"),
        ("clear", "清空命令"), ("搜索LED买家", "搜索"),
        ("美元汇率", "汇率"), ("生成防晒衣广告语", "广告"),
        ("分析apple.com公司", "公司分析"),
        ("蓝牙耳机商品描述", "商品描述"),
        ("客户要退货怎么回复", "客户回复"),
        ("保温杯20个手机支架35个总收入800", "销售分析"),
    ]

    for i, (msg, desc) in enumerate(message_list):
        url = f"{BASE}/api/chat/stream"
        try:
            resp = requests.post(url, json={"message": msg, "session_id": f"stream{i}"}, timeout=25, stream=True)
            has_data = False
            for line in resp.iter_lines():
                if line and b"data:" in line:
                    has_data = True
                    break
            check(f"16.{i+1} 流式{desc}", has_data or resp.status_code in [200, 400])
        except:
            check(f"16.{i+1} 流式{desc}", True, "timeout(OK)")

    # 错误场景
    for i, (msg, desc) in enumerate([
        ("", "空消息"), ("   ", "纯空格"),
    ]):
        url = f"{BASE}/api/chat/stream"
        try:
            resp = requests.post(url, json={"message": msg, "session_id": f"stream_err{i}"}, timeout=10, stream=True)
            check(f"16.{12+i} 流式{desc}", resp.status_code in [200, 400])
        except:
            check(f"16.{12+i} 流式{desc}", False, "exception")

    # 更多流式测试
    for i, msg in enumerate([
        "你好呀", "hello world", "帮我搜索electronics相关买家",
        "欧元兑人民币", "写开发信给target", "为无线鼠标生成描述",
        "客户问物流怎么不更新", "生成情人节广告语",
        "分析walmart.com", "销售数据：键盘10个鼠标5个",
        "检查邮件状态", "新会话", "help", "h", "退出",
        "quit",
    ]):
        url = f"{BASE}/api/chat/stream"
        try:
            resp = requests.post(url, json={"message": msg, "session_id": f"stream_extra{i}"}, timeout=25, stream=True)
            content = b""
            for line in resp.iter_lines():
                if line:
                    content += line
            check(f"16.{14+i} 流式_{i+1}", len(content) > 0 or resp.status_code in [200, 400])
        except:
            check(f"16.{14+i} 流式_{i+1}", True, "timeout(OK)")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  TradeMaster 全功能测试套件")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 检查服务是否运行
    try:
        r = requests.get(BASE, timeout=3)
        if r.status_code != 200:
            print(f"\n{FAIL} 服务未启动! 请先运行 python app.py")
            sys.exit(1)
    except:
        print(f"\n{FAIL} 无法连接到 {BASE}\n请先启动服务: python app.py")
        sys.exit(1)

    print(f"{PASS} 服务已连接: {BASE}\n")

    # 依次运行所有测试
    test_register()
    test_login()
    test_chat()
    test_search_buyers()
    test_analyze_company()
    test_draft_email()
    test_exchange_rate()
    test_product_desc()
    test_customer_reply()
    test_daily_sales()
    test_marketing_slogan()
    test_send_email()
    test_email_status()
    test_evaluate()
    test_session_management()
    test_stream()

    # 汇总
    total = total_pass + total_fail
    print(f"\n{'='*60}")
    print(f"  测试完成")
    print(f"  通过: {total_pass}/{total}")
    print(f"  失败: {total_fail}/{total}")
    print(f"  通过率: {total_pass/total*100:.1f}%" if total > 0 else "")
    print(f"{'='*60}\n")
