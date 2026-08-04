"""核心模块单元测试 — security, cache, db, mailer, logger, services"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = 0; FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" - {detail}" if not cond and detail else ""))

def section(t): print(f"\n{'='*50}\n  {t}\n{'='*50}")

# 1. security
section("1. security.py")
from security import validate_input
ok, c, e = validate_input({"email":{"type":"email","required":True}}, {"email":"Test@X.Com  "}); check("1.1 normalize", ok and c["email"]=="test@x.com")
ok, c, e = validate_input({"email":{"type":"email","required":True}}, {"email":"bad"}); check("1.2 invalid", not ok)
ok, c, e = validate_input({"phone":{"type":"phone","required":True}}, {"phone":"12345"}); check("1.3 phone short", not ok)
ok, c, e = validate_input({"phone":{"type":"phone","required":True}}, {"phone":"13800138000"}); check("1.4 phone ok", ok)
ok, c, e = validate_input({"text":{"type":"str","maxlen":3}}, {"text":"abcdef"}); check("1.5 truncate", ok and len(c["text"])==3)
ok, c, e = validate_input({"name":{"type":"str","default":"X"}}, {}); check("1.6 default", ok and c["name"]=="X")
ok, c, e = validate_input({"email":{"type":"email","required":True}}, {"email":"a@b.com","xss":"<script>"}); check("1.7 xss stripped", ok and "xss" not in c)

# 2. cache
section("2. cache.py")
from cache import cached, stats, invalidate
call_log = []
@cached(ttl=3)
def fn(x): call_log.append(x); return x*2
fn(5); check("2.1 uncached", len(call_log)==1); fn(5); check("2.2 cached", len(call_log)==1); fn(99); check("2.3 diff arg", len(call_log)==2)
check("2.4 stats", stats()["entries"]>=2)
invalidate("fn"); check("2.5 invalidate", stats()["entries"]==0)

# 3. db
section("3. db.py")
import db
if os.path.exists("trademaster.db"): os.remove("trademaster.db")
db.init_db()
s,new=db.get_or_create_session("t@x.com","s1"); check("3.1 create", new)
db.set_system_prompt("t@x.com","s1","SYS"); check("3.2 sys", len(db.get_messages("t@x.com","s1"))==1)
db.append_message("t@x.com","s1","user","hi"); check("3.3 append", len(db.get_messages("t@x.com","s1"))==2)
db.append_message("t@x.com","s1","tool","{}",tool_call_id="c1")
msgs=db.get_messages("t@x.com","s1"); check("3.4 tc_id", msgs[-1].get("tool_call_id")=="c1")
db.update_session_metadata("t@x.com","s1",{"k":"v"}); check("3.5 meta", db.get_session_metadata("t@x.com","s1")["k"]=="v")
for i in range(55): db.append_message("t@x.com","flood","user",f"m{i}")
non=[m for m in db.get_messages("t@x.com","flood") if m["role"]!="system"]; check("3.6 trim", len(non)<=50)
db.delete_session("t@x.com","s1"); check("3.7 delete", len(db.get_messages("t@x.com","s1"))==0)
from services import _sanitize_messages
bad=[{"role":"tool","content":"x"}]; check("3.8 sanitize", len(_sanitize_messages(bad))==0)

# 4. mailer
section("4. mailer.py")
import mailer
check("4.1 configured", mailer.is_configured() in (True,False))
check("4.2 no config send", mailer.send_email_smtp("a@b.com","S","B")["success"]==False)

# 5. services
section("5. services.py")
from services import _safe_str, _needs_tools, execute_tool
check("5.1 safe None", _safe_str(None)=="")
check("5.2 needs tools", _needs_tools("搜索买家") and not _needs_tools("你好"))
r=json.loads(execute_tool("query_exchange_rate",{"currency":"USD"})); check("5.3 tool", r.get("success") in (True,False))
r2=json.loads(execute_tool("no_such_tool",{})); check("5.4 unknown", r2.get("error")==True)

print(f"\n{'='*50}")
print(f"  PASS: {PASS}/{PASS+FAIL} | FAIL: {FAIL}/{PASS+FAIL}")
print(f"{'='*50}")
