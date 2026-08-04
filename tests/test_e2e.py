"""全功能E2E自动测试 + 自动修复"""
import requests, json, time, sys, os, io, traceback

BASE = "http://127.0.0.1:5000"
s = requests.Session()
s.trust_env = False
passed = 0
failed = 0
fixes = 0

def test(name, fn):
    global passed, failed, fixes
    try:
        result = fn()
        if result is True or result is None:
            passed += 1
            print(f"  ✅ {name}")
        elif isinstance(result, str) and result.startswith("FIXED:"):
            passed += 1; fixes += 1
            print(f"  🔧 {name} → {result}")
        else:
            failed += 1
            print(f"  ❌ {name}: {result}")
    except Exception as e:
        failed += 1
        print(f"  💥 {name}: {str(e)[:100]}")

# ============================================================
print("\n" + "="*60)
print("1. 认证系统 (Auth)")
print("="*60)

def test_register():
    r = s.post(f"{BASE}/api/register", json={
        "email":"autotest@trade.com","password":"test1234","phone":"13900000001",
        "product":"bluetooth earphone","identity":"seller"})
    d = r.json()
    if d.get("success") or "已注册" in d.get("error",""):
        return True
    return f"Register failed: {d}"

def test_login():
    r = s.post(f"{BASE}/api/login", json={"email":"autotest@trade.com","password":"test1234"})
    d = r.json()
    if d.get("success"): return True
    # Try register then login
    s.post(f"{BASE}/api/register", json={
        "email":"autotest@trade.com","password":"test1234","phone":"13900000001",
        "product":"bluetooth earphone","identity":"seller"})
    r = s.post(f"{BASE}/api/login", json={"email":"autotest@trade.com","password":"test1234"})
    d = r.json()
    if d.get("success"): return True
    return f"Login failed: {d}"

def test_demo_login():
    r = s.post(f"{BASE}/api/login", json={"email":"demo@trademaster.com","password":"demo2024"})
    d = r.json()
    if d.get("success"): return True
    # Auto-fix: register demo
    s.post(f"{BASE}/api/register", json={
        "email":"demo@trademaster.com","password":"demo2024","phone":"13800138001",
        "product":"bluetooth earphone","identity":"seller"})
    r = s.post(f"{BASE}/api/login", json={"email":"demo@trademaster.com","password":"demo2024"})
    if r.json().get("success"): return "FIXED: demo account re-registered"
    return f"Demo login failed: {r.json()}"

test("注册", test_register)
test("登录", test_login)
test("Demo登录", test_demo_login)

# ============================================================
print("\n" + "="*60)
print("2. AI对话 (Chat)")
print("="*60)

def test_chat_hi():
    r = s.post(f"{BASE}/api/chat", json={"message":"hi","session_id":"autotest"}, timeout=45)
    d = r.json()
    return len(d.get("reply","")) > 5

def test_chat_search():
    r = s.post(f"{BASE}/api/chat",
        json={"message":"搜索蓝牙耳机买家","session_id":"autotest2","user_email":"autotest@trade.com"},
        timeout=90)
    d = r.json()
    reply = d.get("reply","")
    # Should have content, not error
    if d.get("error"): return f"Chat error: {d.get('message','')}"
    return len(reply) > 20 or len(d.get("tool_calls",[])) > 0

def test_chat_stream():
    r = s.post(f"{BASE}/api/chat/stream",
        json={"message":"hi","session_id":"autotest_stream"},
        timeout=30, stream=True)
    content = b""
    for chunk in r.iter_content():
        content += chunk
        if b"[DONE]" in content or b"done" in content: break
    return len(content) > 10

test("对话(hi)", test_chat_hi)
test("搜索买家", test_chat_search)
test("SSE流式", test_chat_stream)

# ============================================================
print("\n" + "="*60)
print("3. 仪表盘 & 工作流 (Dashboard)")
print("="*60)

def test_dashboard():
    r = s.post(f"{BASE}/api/dashboard", json={"user_email":"autotest@trade.com"})
    d = r.json()
    if not d.get("success"): return f"Dashboard failed: {d}"
    has_shows = len(d.get("tradeshows",[])) > 0
    has_certs = len(d.get("certifications",[])) > 0
    return has_shows and has_certs

def test_workflow():
    r = s.post(f"{BASE}/api/workflow/status", json={"user_email":"autotest@trade.com"})
    d = r.json()
    if not d.get("success"): return f"Workflow status failed"
    # Test update
    r2 = s.post(f"{BASE}/api/workflow/update", json={"user_email":"autotest@trade.com","stage":2})
    return r2.json().get("success")

def test_preferences():
    r = s.post(f"{BASE}/api/preferences", json={"user_email":"autotest@trade.com","update":True,"search_query":"bluetooth earphone Germany"})
    d = r.json()
    return d.get("success") and "bluetooth" in str(d.get("preferences",{}))

test("仪表盘数据", test_dashboard)
test("工作流状态", test_workflow)
test("用户偏好", test_preferences)

# ============================================================
print("\n" + "="*60)
print("4. 联系人管理 (Contacts)")
print("="*60)

def test_contact_add():
    r = s.post(f"{BASE}/api/contacts/add", json={
        "user_email":"autotest@trade.com","company_name":"Test GmbH",
        "email":"test@test.de","country":"Germany","product_interest":"TWS"})
    d = r.json()
    return d.get("success")

def test_contact_list():
    r = s.post(f"{BASE}/api/contacts/list", json={"user_email":"autotest@trade.com"})
    d = r.json()
    return d.get("success") and len(d.get("contacts",[])) > 0

def test_contact_stats():
    r = s.post(f"{BASE}/api/contacts/stats", json={"user_email":"autotest@trade.com"})
    d = r.json()
    return d.get("success")

test("添加联系人", test_contact_add)
test("联系人列表", test_contact_list)
test("联系人统计", test_contact_stats)

# ============================================================
print("\n" + "="*60)
print("5. 邮件系统 (Email)")
print("="*60)

def test_send_email():
    r = s.post(f"{BASE}/api/send_email", json={
        "to_email":"test@example.com","subject":"Test","body":"Hello world",
        "user_email":"autotest@trade.com"})
    d = r.json()
    return d.get("success")

def test_email_stats():
    r = s.post(f"{BASE}/api/email/stats", json={"user_email":"autotest@trade.com"})
    d = r.json()
    return d.get("success")

def test_smtp_settings():
    r = s.get(f"{BASE}/api/email/smtp_settings")
    d = r.json()
    return d.get("success")

test("发送邮件", test_send_email)
test("邮件统计", test_email_stats)
test("SMTP设置", test_smtp_settings)

# ============================================================
print("\n" + "="*60)
print("6. 心情玩偶 (Mood Doll)")
print("="*60)

def test_doll_list():
    r = s.get(f"{BASE}/api/doll/list")
    d = r.json()
    return d.get("success") and len(d.get("dolls",[])) == 5

def test_doll_greet():
    r = s.post(f"{BASE}/api/doll/greet", json={"doll_id":"cheerful_bear","type":"auto"})
    d = r.json()
    return d.get("success") and len(d.get("greeting","")) > 5

def test_doll_chat():
    r = s.post(f"{BASE}/api/doll/chat", json={"message":"hello","doll_id":"cheerful_bear"}, timeout=45)
    d = r.json()
    return d.get("success") and len(d.get("reply","")) > 3

test("玩偶列表(5个)", test_doll_list)
test("玩偶问候", test_doll_greet)
test("玩偶对话", test_doll_chat)

# ============================================================
print("\n" + "="*60)
print("7. 展会情报 (Trade Intelligence)")
print("="*60)

def test_trade_knowledge():
    from tools import search_trade_knowledge
    r = json.loads(search_trade_knowledge("bluetooth earphone"))
    return r.get("success") and len(r.get("tradeshows",[])) > 0

def test_exchange_rate():
    r = s.post(f"{BASE}/api/chat", json={"message":"美元汇率","session_id":"rate_test"}, timeout=30)
    d = r.json()
    return len(d.get("reply","")) > 10

test("展会知识检索", test_trade_knowledge)
test("汇率查询", test_exchange_rate)

# ============================================================
print("\n" + "="*60)
print("8. 健康检查 & API文档")
print("="*60)

def test_health():
    r = s.get(f"{BASE}/api/health")
    d = r.json()
    return d.get("status") == "ok"

def test_api_docs():
    r = s.get(f"{BASE}/api/docs")
    d = r.json()
    return d.get("service") == "TradeMaster 外贸通"

def test_demo_help():
    r = s.get(f"{BASE}/api/demo/help")
    d = r.json()
    return d.get("success") and len(d.get("scenarios",[])) > 0

test("健康检查", test_health)
test("API文档", test_api_docs)
test("演示指南", test_demo_help)

# ============================================================
print("\n" + "="*60)
print("9. 页面渲染")
print("="*60)

def test_homepage():
    r = s.get(f"{BASE}/")
    html = r.text
    checks = ["chat-container","auth-overlay","mood-doll","mood-cloud",
              "doll-picker-overlay","input-toolbar","sidebar","btnDemoLogin"]
    missing = [c for c in checks if c not in html]
    if missing: return f"Missing elements: {missing}"
    return True

def test_div_balance():
    r = s.get(f"{BASE}/")
    html = r.text
    opens = html.count("<div")
    closes = html.count("</div>")
    if opens != closes: return f"Div imbalance: {opens} opens vs {closes} closes"
    return True

def test_static_files():
    for path in ["/static/css/style.css","/static/js/app.js"]:
        r = s.get(f"{BASE}{path}")
        if r.status_code != 200: return f"Static file {path} returned {r.status_code}"
    return True

test("主页渲染", test_homepage)
test("Div平衡", test_div_balance)
test("静态资源", test_static_files)

# ============================================================
print("\n" + "="*60)
print(f"结果: {passed} 通过 / {failed} 失败 / {fixes} 自动修复")
print("="*60)

if failed > 0:
    sys.exit(1)
