"""
共享服务层 — Agent 循环 + API 调用 + 邮件辅助
用户系统 → user_service.py
提示词构建 → prompt_service.py
"""
import os
import json
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 异步线程池（最多 4 个并发 LLM 调用）
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="llm")

# ============================================================
# 多 API 提供商配置（自动故障切换）
# ============================================================
http_session = requests.Session()
http_session.trust_env = False  # 绕过系统代理直连API
MAX_ITERATIONS = 3

def _build_providers():
    """从环境变量构建 API 提供商列表"""
    providers = []
    # 主 API
    key = os.getenv("LLM_API_KEY") or os.getenv("SYNSCALE_API_KEY")
    url = os.getenv("LLM_API_URL") or "http://synscale.onesyn.ai/v1/chat/completions"
    model = os.getenv("LLM_MODEL") or os.getenv("SYNSCALE_MODEL_NAME") or "deepseek-v4-pro"
    if key:
        providers.append({"key": key, "url": url, "model": model, "name": "primary"})
    # 备用 API 1
    for i in range(1, 5):
        bk = os.getenv(f"LLM_BACKUP{i}_KEY")
        bu = os.getenv(f"LLM_BACKUP{i}_URL")
        bm = os.getenv(f"LLM_BACKUP{i}_MODEL")
        if bk and bu:
            providers.append({"key": bk, "url": bu, "model": bm or "deepseek-chat", "name": f"backup{i}"})
    return providers

LLM_PROVIDERS = _build_providers()
_provider_health = {}  # 记录各 provider 的健康状态

def get_provider_status():
    """获取所有 API 提供商状态"""
    return _provider_health

# ============================================================
# 邮件后端
# ============================================================
from email_providers.local import LocalEmailProvider
_email_provider = LocalEmailProvider()

# ============================================================
# 用户系统（委托给 user_service）
# ============================================================
from user_service import (
    get_user, _load_users, _save_users, _safe_str,
    _hash_password, _check_password, authenticate_user,
)

# ============================================================
# 系统提示词 + 工具定义
# ============================================================
from tools import TOOL_FUNCTIONS, TOOL_DESCRIPTIONS
from prompt_service import build_system_prompt

# ============================================================
# 工具调用
# ============================================================
import time as _time

def execute_tool(tool_name, tool_args):
    if tool_name not in TOOL_FUNCTIONS:
        return json.dumps({"error": True, "message": f"Unknown tool: {tool_name}"}, ensure_ascii=False)
    t0 = _time.time()
    try:
        result = TOOL_FUNCTIONS[tool_name](**tool_args)
        from logger import log_tool_call
        log_tool_call(tool_name, "", (_time.time() - t0) * 1000, True)
        return result
    except Exception as e:
        from logger import log_tool_call
        log_tool_call(tool_name, "", (_time.time() - t0) * 1000, False)
        return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)

# ============================================================
# 异步辅助
# ============================================================

def run_async(fn, *args, **kwargs):
    """在线程池中异步执行函数，返回 Future 对象"""
    return _executor.submit(fn, *args, **kwargs)


def wait_all(futures, timeout=60):
    """等待所有 Future 完成，返回 [(future, result)]"""
    results = []
    for f in as_completed(futures, timeout=timeout):
        try:
            results.append((f, f.result()))
        except Exception as e:
            results.append((f, {"error": str(e)}))
    return results

# ============================================================
# API 调用
# ============================================================
def _call_one_provider(provider, messages, tools=None):
    """调用单个 API 提供商"""
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {provider['key']}"}
    # Kimi 推理模型需要 temperature=1
    temp = 1.0 if "kimi" in provider.get("model","").lower() else 0.6
    payload = {"model": provider["model"], "messages": messages, "temperature": temp, "max_tokens": 2000}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    else:
        payload["temperature"] = temp
        payload["max_tokens"] = 800

    resp = http_session.post(provider["url"], headers=headers, json=payload, timeout=45)
    if resp.status_code == 200:
        _provider_health[provider["name"]] = {"status": "ok", "last_ok": _time.time()}
        return resp.json()
    return {"error": True, "status_code": resp.status_code, "details": resp.text[:200],
            "provider": provider["name"]}


def call_synscale(messages, tools=None, retries=0):
    """
    多 API 提供商自动故障切换。
    主 API 失败 → 自动尝试备用 API 1 → 备用 API 2 → ...
    """
    if not LLM_PROVIDERS:
        return {"error": True, "message": "未配置任何 LLM API。请在 .env 中设置 LLM_API_KEY 和 LLM_API_URL。"}

    err_names = {500:"服务器内部错误", 502:"网关错误", 503:"服务暂时不可用", 504:"网关超时"}
    providers_tried = []

    for provider in LLM_PROVIDERS:
        # 跳过最近1分钟内失败的 provider
        health = _provider_health.get(provider["name"], {})
        last_fail = health.get("last_fail", 0)
        if last_fail and _time.time() - last_fail < 10:
            providers_tried.append(f"{provider['name']}(冷却中)")
            continue

        result = _call_one_provider(provider, messages, tools)
        if "error" not in result:
            return result

        # 记录失败
        sc = result.get("status_code", 0)
        _provider_health[provider["name"]] = {"status": f"error:{sc}", "last_fail": _time.time()}

        if 500 <= sc < 600 or sc in (401, 403):
            # 5xx + 认证错误 → 尝试下一个 provider（可能是密钥过期/占位符）
            name = err_names.get(sc, f"HTTP {sc}")
            providers_tried.append(f"{provider['name']}:{name}")
            continue
        else:
            # 其他4xx → 不重试
            name = err_names.get(sc, f"HTTP {sc}")
            return {"error": True, "message": f"API{name}({sc})", "details": result.get("details", "")}

    # 所有 provider 都失败
    tried_str = " → ".join(providers_tried) if providers_tried else "无可用提供商"
    return {
        "error": True,
        "message": f"所有API提供商均不可用（尝试了 {len(LLM_PROVIDERS)} 个）。\n\n路径：{tried_str}\n\n原因：上游AI服务商过载/维护，与你的网络无关。\n解决：等待1-3分钟后重试。可配置多个API密钥实现自动切换。"
    }

def call_synscale_stream(messages, tools=None):
    """流式 API 调用 — 多提供商自动故障切换"""
    if not LLM_PROVIDERS:
        yield {"error": True, "message": "未配置任何 LLM API。"}
        return

    for provider in LLM_PROVIDERS:
        health = _provider_health.get(provider["name"], {})
        if health.get("last_fail", 0) and _time.time() - health["last_fail"] < 60:
            continue

        for delta in _stream_one_provider(provider, messages, tools):
            if "error" in delta:
                sc = delta.get("status_code", 0)
                _provider_health[provider["name"]] = {"status": f"error:{sc}", "last_fail": _time.time()}
                if 500 <= sc < 600 or sc in (401, 403):
                    break  # 尝试下一个 provider（含密钥过期/占位符）
                yield delta
                return
            yield delta
        else:
            return  # 成功完成

    yield {"error": True, "message": "所有API提供商均不可用，请稍后重试。"}


def _stream_one_provider(provider, messages, tools=None):
    """流式调用单个提供商"""
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {provider['key']}"}
    temp = 1.0 if "kimi" in provider.get("model","").lower() else 0.6
    payload = {"model": provider["model"], "messages": messages, "temperature": temp, "max_tokens": 2000, "stream": True}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    else:
        payload["temperature"] = temp
        payload["max_tokens"] = 800

    try:
        resp = http_session.post(provider["url"], headers=headers, json=payload, timeout=60, stream=True)
        if resp.status_code == 200:
            _provider_health[provider["name"]] = {"status": "ok", "last_ok": _time.time()}
            for line in resp.iter_lines():
                if not line: continue
                line_str = line.decode("utf-8", errors="replace")
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    if data_str.strip() == "[DONE]": return
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices", [])
                    if choices:
                        yield choices[0].get("delta", {})
        else:
            err_names = {500:"服务器内部错误", 502:"网关错误", 503:"服务暂时不可用", 504:"网关超时"}
            name = err_names.get(resp.status_code, f"HTTP {resp.status_code}")
            yield {"error": True, "status_code": resp.status_code,
                   "message": f"API{name}({resp.status_code})，切换备用服务...",
                   "details": resp.text[:200], "provider": provider["name"]}
    except Exception as e:
        yield {"error": True, "status_code": 0,
               "message": f"连接失败：{str(e)[:100]}，切换备用服务...",
               "provider": provider["name"]}

    # 以下是旧 stream 代码的残留清理
    # 原 call_synscale_stream 函数已合并到上面的 failover 逻辑中
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {SYNSCALE_API_KEY}"}
    payload = {"model": MODEL_NAME, "messages": messages, "temperature": 0.6, "max_tokens": 2000, "stream": True}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    else:
        payload["temperature"] = 0.4
        payload["max_tokens"] = 800

    last_error = None
    for attempt in range(retries + 1):
        if attempt > 0:
            _time.sleep(1.5 * attempt)
        try:
            resp = http_session.post(SYNSCALE_API_URL, headers=headers, json=payload, timeout=60, stream=True)
            if resp.status_code == 200:
                break
            if 500 <= resp.status_code < 600:
                err_names = {500:"服务器内部错误", 502:"网关错误", 503:"服务暂时不可用", 504:"网关超时"}
                name = err_names.get(resp.status_code, f"HTTP {resp.status_code}")
                last_error = {"error": True, "message": f"API{name}({resp.status_code})，重试中...", "details": resp.text[:200]}
                continue
            yield {"error": True, "message": f"API错误({resp.status_code})：{resp.text[:150]}", "details": resp.text[:200]}
            return
        except Exception as e:
            yield {"error": True, "message": f"Request failed: {str(e)}"}
            return

    if last_error and resp.status_code != 200:
        yield {"error": True, "message": "API服务暂时不可用(503)，已重试仍失败。\n\n含义：API服务商(SynScale)过载/维护中。\n解决：等待1-3分钟后重试。与你的网络无关。"}
        return

    # 流式读取
    try:
        for line in resp.iter_lines():
            if not line: continue
            line_str = line.decode("utf-8", errors="replace")
            if line_str.startswith("data: "):
                data_str = line_str[6:]
                if data_str.strip() == "[DONE]": break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices", [])
                if choices:
                    yield choices[0].get("delta", {})
    except Exception as e:
        yield {"error": True, "message": f"Stream failed: {str(e)}"}

# ============================================================
# 简单查询判断
# ============================================================
SIMPLE_QUERIES = {
    '你好', 'hello', 'hi', 'hey', '谢谢', 'thank', '你是谁', 'what are you',
    '再见', 'bye', 'goodbye', '晚安', '早上好', '晚上好', 'good morning',
    'good evening', 'good night', '介绍', 'introduce',
}

def _needs_tools(user_input):
    lower = user_input.lower().strip()
    for kw in SIMPLE_QUERIES:
        if kw in lower:
            return False
    return True

# ============================================================
# Agent 循环
# ============================================================
import db

def _sanitize_messages(messages):
    """清理 DB 加载的损坏消息：移除孤立的 tool 消息（缺 tool_call_id）"""
    return [m for m in messages if not (m.get("role") == "tool" and not m.get("tool_call_id", "").strip())]


def run_agent(user_input, session_id="default", use_tools=True, user_email=None):
    sid = user_email or session_id or "default"
    ue = user_email or ""
    messages = _sanitize_messages(db.get_messages(ue, sid))
    if not messages:
        system_content = build_system_prompt(user_email)
        db.set_system_prompt(ue, sid, system_content)
        messages = [{"role": "system", "content": system_content}]

    messages.append({"role": "user", "content": user_input})
    db.append_message(ue, sid, "user", user_input)

    iteration = 0
    tool_calls_log = []

    while iteration < MAX_ITERATIONS:
        iteration += 1
        response = call_synscale(messages, tools=TOOL_DESCRIPTIONS if use_tools else None)
        if "error" in response:
            error_msg = f"抱歉，发生了错误：{response.get('message', 'Unknown error')}"
            messages.append({"role": "assistant", "content": error_msg})
            db.append_message(ue, sid, "assistant", error_msg)
            return {"reply": error_msg, "tool_calls": tool_calls_log}

        choices = response.get("choices", [])
        if not choices:
            error_msg = "抱歉，未能获取回复"
            messages.append({"role": "assistant", "content": error_msg})
            db.append_message(ue, sid, "assistant", error_msg)
            return {"reply": error_msg, "tool_calls": tool_calls_log}

        message = choices[0].get("message", {})
        assistant_content = message.get("content", "")
        tool_calls = message.get("tool_calls", [])

        if tool_calls:
            messages.append({"role": "assistant", "content": assistant_content, "tool_calls": tool_calls})
            db.append_message(ue, sid, "assistant", assistant_content, tool_calls)
            for tc in tool_calls:
                fn = tc.get("function", {})
                tool_name = fn.get("name", "")
                tool_call_id = tc.get("id") or f"call_{tool_name}_{iteration}"
                try: tool_args = json.loads(fn.get("arguments", "{}"))
                except json.JSONDecodeError: tool_args = {}
                result = execute_tool(tool_name, tool_args)
                try: parsed = json.loads(result) if isinstance(result, str) else result
                except (json.JSONDecodeError, TypeError): parsed = result
                tool_calls_log.append({"tool": tool_name, "args": tool_args, "result": parsed})
                messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": result})
                db.append_message(ue, sid, "tool", result, tool_call_id=tool_call_id)
        else:
            messages.append({"role": "assistant", "content": assistant_content})
            db.append_message(ue, sid, "assistant", assistant_content)
            return {"reply": assistant_content, "tool_calls": tool_calls_log}

    timeout_msg = "抱歉，处理超时，请简化您的问题后重试"
    messages.append({"role": "assistant", "content": timeout_msg})
    db.append_message(ue, sid, "assistant", timeout_msg)
    return {"reply": timeout_msg, "tool_calls": tool_calls_log}

def run_agent_stream(user_input, session_id="default", use_tools=True, user_email=None):
    sid = user_email or session_id or "default"
    ue = user_email or ""
    messages = _sanitize_messages(db.get_messages(ue, sid))
    if not messages:
        system_content = build_system_prompt(user_email)
        db.set_system_prompt(ue, sid, system_content)
        messages = [{"role": "system", "content": system_content}]
    messages.append({"role": "user", "content": user_input})
    db.append_message(ue, sid, "user", user_input)

    iteration = 0
    total_tool_count = 0
    yield {"type": "thinking", "message": "正在理解您的问题..."}

    while iteration < MAX_ITERATIONS:
        iteration += 1
        full_content = ""
        tool_call_chunks = {}

        for delta in call_synscale_stream(messages, tools=TOOL_DESCRIPTIONS if use_tools else None):
            if "error" in delta:
                yield {"type": "error", "message": delta.get("message", "Unknown error")}
                return
            content = delta.get("content", "")
            if content:
                full_content += content
                yield {"type": "text", "content": content}
            for tc in delta.get("tool_calls", []):
                idx = tc.get("index", 0)
                if idx not in tool_call_chunks:
                    tool_call_chunks[idx] = {"id": "", "name": "", "arguments": ""}
                if "id" in tc and tc["id"]:
                    tool_call_chunks[idx]["id"] = tc["id"]
                func = tc.get("function", {})
                if "name" in func and func["name"]:
                    tool_call_chunks[idx]["name"] = func["name"]
                if "arguments" in func:
                    tool_call_chunks[idx]["arguments"] += func["arguments"]

        if tool_call_chunks:
            tool_calls = [tool_call_chunks[i] for i in sorted(tool_call_chunks.keys())]
            api_tc = [{"id": t["id"], "type": "function", "function": {"name": t["name"], "arguments": t["arguments"]}} for t in tool_calls]
            messages.append({"role": "assistant", "content": full_content, "tool_calls": api_tc})
            db.append_message(ue, sid, "assistant", full_content, api_tc)

            for tc in tool_calls:
                tool_name = tc["name"]
                try: tool_args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError: tool_args = {}
                total_tool_count += 1
                # 确保 tool_call_id 不为空
                tool_call_id = tc.get("id") or f"call_{tool_name}_{total_tool_count}"
                yield {"type": "tool_call", "tool": tool_name, "label": tool_name, "args": tool_args, "step": total_tool_count, "total_steps": len(tool_calls), "round": iteration}
                tool_result = execute_tool(tool_name, tool_args)
                try: parsed = json.loads(tool_result) if isinstance(tool_result, str) else tool_result
                except (json.JSONDecodeError, TypeError): parsed = tool_result
                yield {"type": "tool_result", "tool": tool_name, "result": parsed, "step": total_tool_count, "total_steps": len(tool_calls), "round": iteration}
                messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": tool_result})
                db.append_message(ue, sid, "tool", tool_result, tool_call_id=tool_call_id)
            if iteration < MAX_ITERATIONS:
                yield {"type": "thinking", "message": "正在综合信息生成回复..."}
        else:
            messages.append({"role": "assistant", "content": full_content})
            db.append_message(ue, sid, "assistant", full_content)
            return
    yield {"type": "error", "message": "处理超时，请简化问题后重试"}

# ============================================================
# 邮件工具
# ============================================================
from email_tracker import generate_tracking_pixel

def track_sent_email(user_email, to_email, to_name, subject, body):
    tracking_id = generate_tracking_pixel({"from": user_email, "to": to_email, "subject": subject})
    eid = _email_provider.record_sent(user_email, to_email, to_name, subject, body, tracking_id)
    return eid, tracking_id

def get_user_emails(user_email):
    return _email_provider.get_user_emails(user_email)

def get_pending_followups(user_email):
    return _email_provider.get_pending_followups(user_email)

def update_email_status(user_email, to_email, new_status):
    return _email_provider.update_status(user_email, to_email, new_status)

def get_email_stats(user_email):
    return _email_provider.get_stats(user_email)
