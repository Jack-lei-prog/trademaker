# -*- coding: utf-8 -*-
"""
SQLite 数据库模块 — 线程安全连接池 + 写入重试
支持 Session 持久化、消息历史、会话元数据、KV 通用存储
"""
import sqlite3
import json
import threading
import time as _time
import os
from datetime import datetime

DB_PATH = "trademaster.db"
MAX_MESSAGES = 50  # 每个会话最多保留 50 条消息

# ============================================================
# 线程安全连接池
# ============================================================
_conn_pool = {}
_pool_lock = threading.Lock()


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _get_conn():
    """获取当前线程的数据库连接（线程局部连接池，自动创建表）"""
    tid = threading.get_ident()
    with _pool_lock:
        if tid not in _conn_pool:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=5000")
            _ensure_tables(conn)
            _conn_pool[tid] = conn
        return _conn_pool[tid]


def _execute_with_retry(conn, sql, params=(), max_retries=3):
    """带重试的执行，处理 database is locked"""
    for attempt in range(max_retries):
        try:
            return conn.execute(sql, params)
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                _time.sleep(0.1 * (attempt + 1))
                continue
            raise


def close_all_connections():
    """关闭所有连接（应用关闭时调用）"""
    with _pool_lock:
        for conn in _conn_pool.values():
            try:
                conn.close()
            except Exception:
                pass
        _conn_pool.clear()


# ============================================================
# 表结构
# ============================================================

def _ensure_tables(conn):
    """确保表存在（幂等操作）"""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email  TEXT NOT NULL DEFAULT '',
            session_id  TEXT NOT NULL,
            metadata    TEXT NOT NULL DEFAULT '{}',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            UNIQUE(user_email, session_id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  INTEGER NOT NULL,
            role        TEXT NOT NULL,
            content     TEXT NOT NULL DEFAULT '',
            tool_calls  TEXT,
            tool_call_id TEXT,
            created_at  TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_lookup
            ON sessions(user_email, session_id);

        CREATE INDEX IF NOT EXISTS idx_messages_session
            ON messages(session_id, id);

        CREATE TABLE IF NOT EXISTS kv_store (
            key        TEXT PRIMARY KEY,
            value      TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS contacts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email  TEXT NOT NULL,
            company_name TEXT NOT NULL DEFAULT '',
            contact_person TEXT NOT NULL DEFAULT '',
            email       TEXT NOT NULL DEFAULT '',
            phone       TEXT NOT NULL DEFAULT '',
            website     TEXT NOT NULL DEFAULT '',
            country     TEXT NOT NULL DEFAULT '',
            product_interest TEXT NOT NULL DEFAULT '',
            contact_method TEXT NOT NULL DEFAULT 'email',
            status      TEXT NOT NULL DEFAULT 'pending',
            notes       TEXT NOT NULL DEFAULT '',
            source      TEXT NOT NULL DEFAULT '',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            next_remind_at TEXT NOT NULL DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_contacts_user
            ON contacts(user_email, status);
    """)
    # 迁移：为旧 DB 添加 tool_call_id 列
    try:
        conn.execute("ALTER TABLE messages ADD COLUMN tool_call_id TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists


def init_db():
    """初始化数据库表（调用 _get_conn 自动确保表存在）"""
    conn = _get_conn()
    # 不需要 close，连接池管理生命周期


# ============================================================
# Session CRUD
# ============================================================

def get_or_create_session(user_email="", session_id="default"):
    """
    获取或创建会话，返回 (session_row, is_new)
    """
    sid = user_email or session_id or "default"
    conn = _get_conn()
    now = _now()

    row = _execute_with_retry(conn,
        "SELECT * FROM sessions WHERE user_email=? AND session_id=?",
        (user_email or "", sid)
    ).fetchone()

    if row:
        return dict(row), False

    _execute_with_retry(conn,
        "INSERT INTO sessions (user_email, session_id, metadata, created_at, updated_at) VALUES (?,?,?,?,?)",
        (user_email or "", sid, "{}", now, now)
    )
    conn.commit()

    row = _execute_with_retry(conn,
        "SELECT * FROM sessions WHERE user_email=? AND session_id=?",
        (user_email or "", sid)
    ).fetchone()
    return dict(row), True


def get_session_metadata(user_email="", session_id="default"):
    """获取会话元数据"""
    session, _ = get_or_create_session(user_email, session_id)
    try:
        return json.loads(session.get("metadata", "{}"))
    except (json.JSONDecodeError, TypeError):
        return {}


def update_session_metadata(user_email="", session_id="default", metadata=None):
    """更新会话元数据（合并更新）"""
    if metadata is None:
        return
    conn = _get_conn()
    session, _ = get_or_create_session(user_email, session_id)
    existing = {}
    try:
        existing = json.loads(session.get("metadata", "{}"))
    except (json.JSONDecodeError, TypeError):
        pass
    existing.update(metadata)
    _execute_with_retry(conn,
        "UPDATE sessions SET metadata=?, updated_at=? WHERE id=?",
        (json.dumps(existing, ensure_ascii=False), _now(), session["id"])
    )
    conn.commit()


def delete_session(user_email="", session_id="default"):
    """删除会话及其所有消息（多级回退匹配）"""
    conn = _get_conn()

    rows = []
    if user_email:
        rows = _execute_with_retry(conn,
            "SELECT id FROM sessions WHERE user_email=? AND session_id=?",
            (user_email, session_id)
        ).fetchall()
    if not rows:
        rows = _execute_with_retry(conn,
            "SELECT id FROM sessions WHERE session_id=?",
            (session_id,)
        ).fetchall()
    if not rows and user_email:
        rows = _execute_with_retry(conn,
            "SELECT id FROM sessions WHERE session_id=?",
            (user_email,)
        ).fetchall()

    for r in rows:
        _execute_with_retry(conn, "DELETE FROM messages WHERE session_id=?", (r["id"],))
    for r in rows:
        _execute_with_retry(conn, "DELETE FROM sessions WHERE id=?", (r["id"],))
    conn.commit()


def list_user_sessions(user_email):
    """列出某用户的所有会话"""
    conn = _get_conn()
    rows = _execute_with_retry(conn,
        "SELECT * FROM sessions WHERE user_email=? ORDER BY updated_at DESC",
        (user_email,)
    ).fetchall()
    return [dict(r) for r in rows]


# ============================================================
# Messages CRUD
# ============================================================

def get_messages(user_email="", session_id="default"):
    """获取会话的所有消息"""
    session, is_new = get_or_create_session(user_email, session_id)
    if is_new:
        return []

    conn = _get_conn()
    rows = _execute_with_retry(conn,
        "SELECT * FROM messages WHERE session_id=? ORDER BY id ASC",
        (session["id"],)
    ).fetchall()

    messages = []
    for r in rows:
        msg = {"role": r["role"], "content": r["content"] or ""}
        if r["tool_calls"]:
            try:
                msg["tool_calls"] = json.loads(r["tool_calls"])
            except (json.JSONDecodeError, TypeError):
                pass
        msg["tool_call_id"] = r["tool_call_id"] or ""
        messages.append(msg)
    return messages


def set_system_prompt(user_email="", session_id="default", system_content=""):
    """设置会话的系统提示词"""
    session, _ = get_or_create_session(user_email, session_id)
    conn = _get_conn()

    _execute_with_retry(conn,
        "DELETE FROM messages WHERE session_id=? AND role='system'",
        (session["id"],)
    )
    _execute_with_retry(conn,
        "INSERT INTO messages (session_id, role, content, created_at) VALUES (?,?,?,?)",
        (session["id"], "system", system_content, _now())
    )
    conn.commit()


def append_message(user_email="", session_id="default", role="", content="", tool_calls=None, tool_call_id=None):
    """追加一条消息"""
    session, _ = get_or_create_session(user_email, session_id)
    conn = _get_conn()

    tc_json = json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None
    _execute_with_retry(conn,
        "INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id, created_at) VALUES (?,?,?,?,?,?)",
        (session["id"], role, content or "", tc_json, tool_call_id, _now())
    )
    conn.commit()
    _touch_session(session["id"])
    _trim_messages(session["id"])


def append_messages_batch(user_email="", session_id="default", messages_list=None):
    """批量追加消息（性能优化）"""
    if not messages_list:
        return
    session, _ = get_or_create_session(user_email, session_id)
    conn = _get_conn()

    now = _now()
    for msg in messages_list:
        role = msg.get("role", "")
        content = msg.get("content", "") or ""
        tc_json = json.dumps(msg.get("tool_calls"), ensure_ascii=False) if msg.get("tool_calls") else None
        _execute_with_retry(conn,
            "INSERT INTO messages (session_id, role, content, tool_calls, created_at) VALUES (?,?,?,?,?)",
            (session["id"], role, content, tc_json, now)
        )

    conn.commit()
    _touch_session(session["id"])
    _trim_messages(session["id"])


# ============================================================
# KV 通用存储（替代 JSON 文件存储）
# ============================================================

def kv_get(key: str, default=None):
    """读取 KV 值（自动 JSON 反序列化）"""
    conn = _get_conn()
    row = _execute_with_retry(conn,
        "SELECT value FROM kv_store WHERE key=?", (key,)
    ).fetchone()
    if row:
        try:
            return json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            return default
    return default


def kv_set(key: str, value):
    """写入 KV 值（自动 JSON 序列化）"""
    conn = _get_conn()
    _execute_with_retry(conn,
        "INSERT OR REPLACE INTO kv_store (key, value, updated_at) VALUES (?,?,?)",
        (key, json.dumps(value, ensure_ascii=False), _now())
    )
    conn.commit()


def kv_delete(key: str):
    """删除 KV 键"""
    conn = _get_conn()
    _execute_with_retry(conn,
        "DELETE FROM kv_store WHERE key=?", (key,)
    )
    conn.commit()


# ============================================================
# Internal helpers
# ============================================================

def _touch_session(session_id):
    conn = _get_conn()
    _execute_with_retry(conn,
        "UPDATE sessions SET updated_at=? WHERE id=?",
        (_now(), session_id)
    )
    conn.commit()


def _trim_messages(session_pk):
    """保留最近 MAX_MESSAGES 条非 system 消息 + 所有 system 消息"""
    conn = _get_conn()
    count_row = _execute_with_retry(conn,
        "SELECT COUNT(*) as cnt FROM messages WHERE session_id=? AND role!='system'",
        (session_pk,)
    ).fetchone()

    if count_row and count_row["cnt"] > MAX_MESSAGES:
        excess = count_row["cnt"] - MAX_MESSAGES
        _execute_with_retry(conn, """
            DELETE FROM messages WHERE id IN (
                SELECT id FROM messages
                WHERE session_id=? AND role!='system'
                ORDER BY id ASC LIMIT ?
            )
        """, (session_pk, excess))

    conn.commit()


# ============================================================
# 导入兼容 — 服务层迁移辅助
# ============================================================

def load_users():
    """从 KV 存储加载用户（兼容旧 JSON 文件）"""
    users = kv_get("users")
    if users is not None:
        return users
    # 首次从 JSON 文件迁移
    if os.path.exists("users.json"):
        try:
            with open("users.json", "r", encoding="utf-8") as f:
                users = json.load(f)
            kv_set("users", users)
            return users
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_users(users: dict):
    """保存用户到 KV 存储"""
    kv_set("users", users)


def load_followups():
    """从 KV 存储加载跟进数据"""
    followups = kv_get("followups")
    if followups is not None:
        return followups
    if os.path.exists("inquiry_followups.json"):
        try:
            with open("inquiry_followups.json", "r", encoding="utf-8") as f:
                followups = json.load(f)
            kv_set("followups", followups)
            return followups
        except (json.JSONDecodeError, IOError):
            pass
    return []


def save_followups(data: list):
    """保存跟进数据到 KV 存储"""
    kv_set("followups", data)


# ============================================================
# 客户联系人管理
# ============================================================

def add_contact(user_email: str, company_name: str = "", email: str = "",
                website: str = "", country: str = "", contact_person: str = "",
                phone: str = "", product_interest: str = "",
                contact_method: str = "email", source: str = "", notes: str = "",
                next_remind_days: int = 7) -> int:
    """添加待联系客户，返回 contact_id"""
    conn = _get_conn()
    now = _now()
    remind_at = (datetime.now() + __import__('datetime').timedelta(days=next_remind_days)).strftime("%Y-%m-%d %H:%M:%S")
    _execute_with_retry(conn, """
        INSERT INTO contacts (user_email, company_name, contact_person, email, phone,
            website, country, product_interest, contact_method, status, notes, source,
            created_at, updated_at, next_remind_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (user_email, company_name, contact_person, email, phone, website, country,
          product_interest, contact_method, "pending", notes, source, now, now, remind_at))
    conn.commit()
    return _execute_with_retry(conn, "SELECT last_insert_rowid()").fetchone()[0]


def get_contacts(user_email: str, status: str = "") -> list:
    """获取用户的待联系客户列表"""
    conn = _get_conn()
    if status:
        rows = _execute_with_retry(conn,
            "SELECT * FROM contacts WHERE user_email=? AND status=? ORDER BY updated_at DESC",
            (user_email, status)).fetchall()
    else:
        rows = _execute_with_retry(conn,
            "SELECT * FROM contacts WHERE user_email=? ORDER BY updated_at DESC",
            (user_email,)).fetchall()
    return [dict(r) for r in rows]


def update_contact(contact_id: int, user_email: str = "", **kwargs) -> bool:
    """更新联系人信息/状态"""
    conn = _get_conn()
    allowed = {"status", "notes", "contact_method", "email", "phone",
               "contact_person", "next_remind_at", "product_interest"}
    updates = {}
    for k, v in kwargs.items():
        if k in allowed:
            updates[k] = v
    if not updates:
        return False
    updates["updated_at"] = _now()
    set_clause = ", ".join(f"{k}=?" for k in updates)
    values = list(updates.values())
    values.append(contact_id)
    if user_email:
        values.append(user_email)
        _execute_with_retry(conn, f"UPDATE contacts SET {set_clause} WHERE id=? AND user_email=?",
                          tuple(values))
    else:
        _execute_with_retry(conn, f"UPDATE contacts SET {set_clause} WHERE id=?",
                          tuple(values))
    conn.commit()
    return True


def delete_contact(contact_id: int, user_email: str = "") -> bool:
    """删除联系人"""
    conn = _get_conn()
    if user_email:
        _execute_with_retry(conn, "DELETE FROM contacts WHERE id=? AND user_email=?",
                          (contact_id, user_email))
    else:
        _execute_with_retry(conn, "DELETE FROM contacts WHERE id=?", (contact_id,))
    conn.commit()
    return True


def get_due_reminders(user_email: str) -> list:
    """获取需要提醒的联系人（超过提醒日期）"""
    conn = _get_conn()
    now = _now()
    rows = _execute_with_retry(conn,
        "SELECT * FROM contacts WHERE user_email=? AND status='pending' AND next_remind_at!='' AND next_remind_at<=? ORDER BY next_remind_at ASC",
        (user_email, now)).fetchall()
    return [dict(r) for r in rows]


# ============================================================
# 邮件审计日志
# ============================================================

def log_email_audit(draft_id, user_email, to_email, subject, body_preview,
                    idempotency_key, success, error=None):
    """记录邮件发送审计日志到 KV 存储"""
    record = {
        "user_email": user_email,
        "confirmed_at": _now(),
        "to_email": to_email,
        "subject": subject,
        "body_snapshot": body_preview[:500],
        "idempotency_key": idempotency_key,
        "success": success,
        "error": error,
    }
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    kv_set(f"email_audit:{ts}:{draft_id}", record)


def get_email_audit_logs(user_email=None, limit=50):
    """查询邮件审计日志（可按用户过滤）"""
    conn = _get_conn()
    prefix = "email_audit:"
    rows = _execute_with_retry(conn,
        "SELECT key FROM kv_store WHERE key LIKE ? ORDER BY key DESC LIMIT ?",
        (f"{prefix}%", limit)
    ).fetchall()
    logs = []
    for r in rows:
        record = kv_get(r["key"])
        if record and (user_email is None or record.get("user_email") == user_email):
            logs.append(record)
    return logs


# ============================================================
# 退订管理
# ============================================================

def is_unsubscribed(email):
    """检查邮箱是否已退订"""
    return kv_get(f"unsub:{email.lower().strip()}") is not None


def add_unsubscribe(email, reason=""):
    """添加退订记录"""
    kv_set(f"unsub:{email.lower().strip()}", {
        "email": email.lower().strip(),
        "reason": reason,
        "unsubscribed_at": _now(),
    })


def remove_unsubscribe(email):
    """移除退订记录（用户重新订阅）"""
    kv_delete(f"unsub:{email.lower().strip()}")


# ============================================================
# 初始化
# ============================================================

init_db()

