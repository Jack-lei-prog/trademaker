"""测试 user_service.py — 用户认证服务"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPasswordHashing:
    """密码哈希测试"""

    def test_hash_and_check(self):
        from user_service import _hash_password, _check_password
        pw = "my_secure_password"
        hashed = _hash_password(pw)
        assert hashed != pw
        assert _check_password(pw, hashed) is True

    def test_check_wrong_password(self):
        from user_service import _hash_password, _check_password
        hashed = _hash_password("correct")
        assert _check_password("wrong", hashed) is False

    def test_check_empty_hash(self):
        from user_service import _check_password
        assert _check_password("anything", "") is False

    def test_hash_is_stable(self):
        from user_service import _hash_password, _check_password
        pw = "test123"
        h1 = _hash_password(pw)
        h2 = _hash_password(pw)
        # bcrypt 每次生成不同的盐，所以哈希不同
        assert h1 != h2
        # 但都能验证
        assert _check_password(pw, h1) is True
        assert _check_password(pw, h2) is True


class TestAuthenticateUser:
    """用户认证测试"""

    def test_auth_success(self):
        from user_service import _load_users, _save_users, _hash_password, authenticate_user
        pw_hash = _hash_password("test_password")
        _save_users({"auth@test.com": {
            "email": "auth@test.com",
            "password_hash": pw_hash,
            "company": "Test Co"
        }})
        user = authenticate_user("auth@test.com", "test_password")
        assert user is not None
        assert user["email"] == "auth@test.com"

    def test_auth_wrong_password(self):
        from user_service import authenticate_user
        user = authenticate_user("auth@test.com", "wrong_password")
        assert user is None

    def test_auth_nonexistent_user(self):
        from user_service import authenticate_user
        user = authenticate_user("noone@test.com", "any_password")
        assert user is None


class TestGetUser:
    def test_get_existing(self):
        from user_service import _save_users, get_user
        _save_users({"find@test.com": {"email": "find@test.com"}})
        user = get_user("find@test.com")
        assert user is not None

    def test_get_nonexistent(self):
        from user_service import get_user
        user = get_user("ghost@test.com")
        assert user is None

    def test_case_insensitive(self):
        from user_service import _save_users, get_user
        _save_users({"case@test.com": {"email": "case@test.com"}})
        user = get_user("CASE@test.com")
        assert user is not None
        assert user["email"] == "case@test.com"


class TestSafeStr:
    def test_normal_string(self):
        from user_service import _safe_str
        assert _safe_str("hello") == "hello"

    def test_none(self):
        from user_service import _safe_str
        assert _safe_str(None) == ""

    def test_non_string(self):
        from user_service import _safe_str
        assert _safe_str(123) == ""

    def test_default_value(self):
        from user_service import _safe_str
        assert _safe_str(None, "fallback") == "fallback"
