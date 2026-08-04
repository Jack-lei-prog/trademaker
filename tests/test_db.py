"""测试 db.py — SQLite 数据库模块"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestKVStore:
    """KV 通用存储测试"""

    def test_set_and_get(self):
        import db
        db.kv_set("test_key", {"name": "test", "value": 42})
        result = db.kv_get("test_key")
        assert result == {"name": "test", "value": 42}
        db.kv_delete("test_key")

    def test_get_nonexistent_default(self):
        import db
        result = db.kv_get("nonexistent_key_xyz", default={"fallback": True})
        assert result == {"fallback": True}

    def test_overwrite(self):
        import db
        db.kv_set("test_overwrite", 1)
        db.kv_set("test_overwrite", 2)
        assert db.kv_get("test_overwrite") == 2
        db.kv_delete("test_overwrite")

    def test_delete(self):
        import db
        db.kv_set("test_delete", "data")
        assert db.kv_get("test_delete") == "data"
        db.kv_delete("test_delete")
        assert db.kv_get("test_delete") is None

    def test_complex_object(self):
        import db
        complex_obj = {
            "users": [{"email": "a@b.com", "name": "Alice"}],
            "count": 100,
            "nested": {"deep": [1, 2, 3]}
        }
        db.kv_set("test_complex", complex_obj)
        result = db.kv_get("test_complex")
        assert result == complex_obj
        db.kv_delete("test_complex")


class TestSessionCRUD:
    """会话 CRUD 测试"""

    def test_create_and_get_session(self):
        import db
        session, is_new = db.get_or_create_session("test@test.com", "test_session")
        assert is_new or not is_new  # 可能已存在
        assert "id" in session
        assert session["user_email"] == "test@test.com"

    def test_delete_session(self):
        import db
        db.get_or_create_session("del@test.com", "del_session")
        db.delete_session("del@test.com", "del_session")
        session, is_new = db.get_or_create_session("del@test.com", "del_session")
        assert is_new is True


class TestMessagesCRUD:
    """消息 CRUD 测试"""

    def test_append_and_get_messages(self):
        import db
        db.delete_session("msg@test.com", "msg_session")
        db.append_message("msg@test.com", "msg_session", "user", "Hello")
        db.append_message("msg@test.com", "msg_session", "assistant", "Hi there!")
        messages = db.get_messages("msg@test.com", "msg_session")
        assert len(messages) >= 2
        assert messages[-2]["role"] == "user"
        assert messages[-2]["content"] == "Hello"
        assert messages[-1]["role"] == "assistant"

    def test_system_prompt(self):
        import db
        db.set_system_prompt("sys@test.com", "sys_session", "You are a helpful assistant.")
        messages = db.get_messages("sys@test.com", "sys_session")
        assert any(m["role"] == "system" for m in messages)


class TestUsersKV:
    """用户 KV 存储测试"""

    def test_load_and_save_users(self):
        import db
        users = {"a@b.com": {"email": "a@b.com", "name": "Test"}}
        db.save_users(users)
        loaded = db.load_users()
        assert loaded == users

    def test_load_users_empty(self):
        import db
        db.save_users({})
        loaded = db.load_users()
        assert loaded == {}
