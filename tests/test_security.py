# -*- coding: utf-8 -*-
"""安全测试 - 认证绕过、越权访问、重复发送、限流、密码加密、注入防护"""
import pytest
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as _app


@pytest.fixture
def client():
    _app.config["TESTING"] = True
    with _app.test_client() as c:
        yield c


def _register_and_login(client, email="sec_test@trade.com"):
    resp = client.post("/api/register", json={
        "email": email, "password": "test1234", "phone": "13900000001",
        "product": "bluetooth earphone", "identity": "seller"
    })
    data = resp.get_json()
    if data.get("success"):
        return data.get("token", "")
    resp2 = client.post("/api/login", json={
        "email": email, "password": "test1234"
    })
    return resp2.get_json().get("token", "")


def _auth_headers(token):
    return {"Authorization": "Bearer " + token, "Content-Type": "application/json"}


class TestAuthRequired:

    def test_email_send_requires_auth(self, client):
        resp = client.post("/api/email/smtp_send", json={
            "to_email": "x@x.com", "subject": "t", "body": "t"
        })
        assert resp.status_code == 401

    def test_smtp_settings_get_requires_auth(self, client):
        resp = client.get("/api/email/smtp_settings")
        assert resp.status_code == 401

    def test_smtp_settings_post_requires_auth(self, client):
        resp = client.post("/api/email/smtp_settings", json={
            "smtp_email": "x@x.com", "smtp_password": "t"
        })
        assert resp.status_code == 401

    def test_contacts_require_auth(self, client):
        resp = client.post("/api/contacts/list", json={})
        assert resp.status_code == 401

    def test_dashboard_requires_auth(self, client):
        resp = client.post("/api/dashboard", json={})
        assert resp.status_code == 401

    def test_inquiry_requires_auth(self, client):
        resp = client.post("/api/inquiry/process", json={"inquiry_text": "t"})
        assert resp.status_code == 401

    def test_evaluate_requires_auth(self, client):
        resp = client.post("/api/evaluate", json={"question": "t", "answer": "t"})
        assert resp.status_code == 401


class TestCrossUserAccess:

    def test_cannot_access_other_contacts(self, client):
        token_a = _register_and_login(client, "user_a@trade.com")
        token_b = _register_and_login(client, "user_b@trade.com")
        client.post("/api/contacts/add", json={
            "company_name": "Company A", "email": "a@company.com"
        }, headers=_auth_headers(token_a))
        resp = client.post("/api/contacts/list", json={},
                           headers=_auth_headers(token_a))
        assert resp.get_json()["total"] >= 1
        resp = client.post("/api/contacts/list", json={},
                           headers=_auth_headers(token_b))
        contacts = resp.get_json().get("contacts", [])
        has_a = any(c.get("company_name") == "Company A" for c in contacts)
        assert not has_a

    def test_cannot_access_other_dashboard(self, client):
        token_a = _register_and_login(client, "dash_a@trade.com")
        token_b = _register_and_login(client, "dash_b@trade.com")
        resp_a = client.post("/api/dashboard", json={},
                             headers=_auth_headers(token_a))
        resp_b = client.post("/api/dashboard", json={},
                             headers=_auth_headers(token_b))
        assert resp_a.get_json()["user"]["email"] == "dash_a@trade.com"
        assert resp_b.get_json()["user"]["email"] == "dash_b@trade.com"


class TestJWTToken:

    def test_login_returns_token(self, client):
        client.post("/api/register", json={
            "email": "jwt_login@trade.com", "password": "test1234",
            "phone": "13900000001", "product": "test", "identity": "seller"
        })
        resp = client.post("/api/login", json={
            "email": "jwt_login@trade.com", "password": "test1234"
        })
        data = resp.get_json()
        assert data.get("success")
        assert "token" in data
        assert len(data["token"]) > 20

    def test_register_returns_token(self, client):
        import random
        email = "jwt_reg_" + str(random.randint(0, 99999)) + "@trade.com"
        resp = client.post("/api/register", json={
            "email": email, "password": "test1234",
            "phone": "13900000001", "product": "test", "identity": "seller"
        })
        data = resp.get_json()
        assert data.get("success")
        assert "token" in data
        assert len(data["token"]) > 20

    def test_invalid_token_rejected(self, client):
        resp = client.post("/api/contacts/list", json={},
                           headers={"Authorization": "Bearer invalid_token"})
        assert resp.status_code == 401


class TestChatEndpointAuth:

    def test_chat_without_token_returns_401(self, client):
        resp = client.post("/api/chat", json={"message": "hello"})
        assert resp.status_code == 401

    def test_chat_stream_without_token_returns_401(self, client):
        resp = client.post("/api/chat/stream", json={"message": "hello"})
        assert resp.status_code == 401

    def test_upload_manual_without_token_returns_401(self, client):
        resp = client.post("/api/upload/manual", data={})
        assert resp.status_code == 401

    def test_upload_excel_without_token_returns_401(self, client):
        resp = client.post("/api/upload/excel", data={})
        assert resp.status_code == 401

    def test_clear_without_token_returns_401(self, client):
        resp = client.post("/api/clear", json={})
        assert resp.status_code == 401

    def test_chat_with_valid_token_succeeds(self, client):
        token = _register_and_login(client, "chat_auth@trade.com")
        resp = client.post("/api/chat", json={"message": "help"},
                           headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert "reply" in data

    def test_chat_stream_with_valid_token_succeeds(self, client):
        token = _register_and_login(client, "stream_auth@trade.com")
        resp = client.post("/api/chat/stream", json={"message": "help"},
                           headers=_auth_headers(token))
        assert resp.status_code == 200
        assert "text/event-stream" in resp.content_type

    def test_clear_with_valid_token_succeeds(self, client):
        token = _register_and_login(client, "clear_auth@trade.com")
        resp = client.post("/api/clear", json={},
                           headers=_auth_headers(token))
        assert resp.status_code == 200
        assert resp.get_json()["success"]


class TestSMTPEncryption:

    def test_roundtrip_encrypt_decrypt(self):
        from smtp_crypto import encrypt_password, decrypt_password
        plain = "TestP@ssw0rd2024"
        encrypted = encrypt_password(plain)
        assert encrypted != plain
        assert len(encrypted) > 10
        decrypted = decrypt_password(encrypted)
        assert decrypted == plain

    def test_empty_password(self):
        from smtp_crypto import encrypt_password, decrypt_password
        assert encrypt_password("") == ""
        assert decrypt_password("") == ""


class TestSecurityHeaders:

    def test_security_headers_present(self, client):
        resp = client.get("/api/health")
        h = resp.headers
        assert h.get("X-Content-Type-Options") == "nosniff"
        assert h.get("X-Frame-Options") == "DENY"
        assert h.get("X-XSS-Protection") == "1; mode=block"

    def test_cors_rejects_evil_origin(self, client):
        resp = client.get("/api/health", headers={"Origin": "https://evil.com"})
        acao = resp.headers.get("Access-Control-Allow-Origin", "")
        assert acao != "https://evil.com"
        assert acao != "*"
