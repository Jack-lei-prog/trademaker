# -*- coding: utf-8 -*-
"""
Gmail API 邮件后端
通过 OAuth 2.0 授权，自动同步已发送 + 收件箱回复
基于 SQLite KV 存储替代 JSON 文件
"""
import json
import os
import re
import base64
import requests
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional
from . import BaseEmailProvider


# ============================================================
# Gmail API 配置
# ============================================================
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailEmailProvider(BaseEmailProvider):
    """Gmail API 邮件后端"""

    def __init__(self):
        import db
        self.config = db.kv_get("gmail_config") or {}
        self.tokens = db.kv_get("gmail_tokens") or {}
        self._db = db.kv_get("gmail_emails") or {}
        self._configured = bool(self.config.get("client_id") and self.config.get("client_secret"))

    # ============================================================
    # 配置管理
    # ============================================================

    def _save_config(self):
        import db
        db.kv_set("gmail_config", self.config)

    def _save_tokens(self):
        import db
        db.kv_set("gmail_tokens", self.tokens)

    def _save_db(self):
        import db
        db.kv_set("gmail_emails", self._db)

    def configure(self, client_id: str, client_secret: str, redirect_uri: str = ""):
        """配置 Gmail API 凭证"""
        self.config = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri or "http://127.0.0.1:5000/api/email/gmail/callback",
        }
        self._save_config()
        self._configured = True

    def is_configured(self) -> bool:
        return self._configured

    def get_auth_url(self, user_email: str) -> str:
        """生成 Gmail OAuth 授权 URL"""
        if not self._configured:
            return ""
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = (
            f"client_id={self.config['client_id']}"
            f"&redirect_uri={self.config['redirect_uri']}"
            f"&response_type=code"
            f"&scope={'%20'.join(GMAIL_SCOPES)}"
            f"&access_type=offline"
            f"&prompt=consent"
            f"&state={user_email}"
        )
        return f"{base_url}?{params}"

    def handle_callback(self, code: str, user_email: str) -> bool:
        """处理 OAuth 回调，用 code 换取 token"""
        resp = requests.post("https://oauth2.googleapis.com/token", data={
            "client_id": self.config["client_id"],
            "client_secret": self.config["client_secret"],
            "code": code,
            "redirect_uri": self.config["redirect_uri"],
            "grant_type": "authorization_code",
        }, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            self.tokens[user_email] = {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", ""),
                "expires_at": (datetime.now() + timedelta(seconds=data.get("expires_in", 3600))).isoformat(),
            }
            self._save_tokens()
            return True
        return False

    def _get_access_token(self, user_email: str) -> Optional[str]:
        """获取或刷新 access_token"""
        token = self.tokens.get(user_email, {})
        if not token:
            return None

        expires = token.get("expires_at", "")
        if expires and datetime.now() > datetime.fromisoformat(expires):
            resp = requests.post("https://oauth2.googleapis.com/token", data={
                "client_id": self.config["client_id"],
                "client_secret": self.config["client_secret"],
                "refresh_token": token.get("refresh_token", ""),
                "grant_type": "refresh_token",
            }, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                token["access_token"] = data["access_token"]
                token["expires_at"] = (datetime.now() + timedelta(seconds=data.get("expires_in", 3600))).isoformat()
                self.tokens[user_email] = token
                self._save_tokens()
            else:
                return None

        return token.get("access_token", "")

    def _gmail_api(self, user_email: str, method: str, path: str,
                   params=None, json_body=None, raw_body: str = "") -> Optional[dict]:
        """调用 Gmail API"""
        access_token = self._get_access_token(user_email)
        if not access_token:
            return None

        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"https://gmail.googleapis.com/gmail/v1/{path}"

        if method == "GET":
            r = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            if json_body:
                r = requests.post(url, headers=headers, json=json_body, timeout=10)
            else:
                headers["Content-Type"] = "message/rfc822"
                r = requests.post(url, headers=headers, data=raw_body or "", timeout=15)
        else:
            return None

        if r.status_code in (200, 201):
            return r.json()
        return None

    # ============================================================
    # 发送邮件
    # ============================================================

    def send_via_gmail(self, user_email: str, to_email: str, subject: str,
                       body: str, tracking_pixel_url: str = "") -> Optional[str]:
        """通过 Gmail API 真正发送邮件（含追踪像素）"""
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["From"] = user_email
        msg["To"] = to_email
        msg["Subject"] = subject

        html_body = body.replace("\n", "<br>")
        if tracking_pixel_url:
            html_body += f'<br><img src="{tracking_pixel_url}" width="1" height="1" alt="">'

        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        result = self._gmail_api(user_email, "POST", "users/me/messages/send",
                                 json_body={"raw": raw})
        if result:
            return result.get("id", "")
        return None

    # ============================================================
    # 同步收件箱 — 检测客户回复
    # ============================================================

    def sync_inbox(self, user_email: str) -> List[Dict]:
        """同步收件箱，检测之前发过的邮件是否有回复"""
        if not self._configured:
            return []

        result = self._gmail_api(user_email, "GET", "users/me/messages",
                                 params={"q": "in:inbox newer_than:30d", "maxResults": 50})
        if not result:
            return []

        new_replies = []
        my_emails = self.get_user_emails(user_email)
        my_recipients = {e.get("to", "").lower() for e in my_emails}

        for msg in result.get("messages", []):
            msg_id = msg["id"]
            detail = self._gmail_api(user_email, "GET", f"users/me/messages/{msg_id}",
                                     params={"format": "metadata",
                                             "metadataHeaders": "From,Subject,Date,References,In-Reply-To"})
            if not detail:
                continue

            headers = {}
            for h in detail.get("payload", {}).get("headers", []):
                headers[h["name"].lower()] = h["value"]

            from_addr = headers.get("from", "")
            from_email_match = re.search(r'[\w.+-]+@[\w.-]+', from_addr)
            from_email = from_email_match.group(0).lower() if from_email_match else ""

            if from_email in my_recipients:
                for e in my_emails:
                    if e.get("to", "").lower() == from_email and e.get("status") in ("sent", "no_reply"):
                        self.update_status(user_email, from_email, "replied")
                        new_replies.append({
                            "from": from_email,
                            "subject": headers.get("subject", ""),
                            "replied_at": headers.get("date", self._now()),
                            "original_email_id": e.get("id", ""),
                        })
                        break

        return new_replies

    # ============================================================
    # 基础 CRUD（SQLite KV 存储）
    # ============================================================

    def _db_get_user_emails(self, user_email: str) -> List[Dict]:
        return [v for v in self._db.values() if v.get("from") == user_email]

    def record_sent(self, user_email: str, to_email: str, to_name: str,
                    subject: str, body: str, tracking_id: str = "") -> str:
        now = self._now()
        eid = f"gmail_{user_email}_{to_email}_{now.replace(' ', '_').replace(':', '-')}"
        self._db[eid] = {
            "id": eid, "from": user_email, "to": to_email,
            "to_name": to_name, "subject": subject,
            "body_preview": body[:200], "sent_at": now,
            "status": "sent", "followups": [],
            "tracking_id": tracking_id,
            "opened_at": "", "opened_count": 0,
            "replied_at": "", "intent": "",
            "provider": "gmail",
        }
        self._save_db()
        return eid

    def get_user_emails(self, user_email: str) -> List[Dict]:
        return self._db_get_user_emails(user_email)

    def get_pending_followups(self, user_email: str) -> List[Dict]:
        now = datetime.now()
        pending = []
        for e in self._db_get_user_emails(user_email):
            if e.get("status") in ("sent", "no_reply"):
                try:
                    days = (now - datetime.strptime(e["sent_at"], "%Y-%m-%d %H:%M")).days
                except (ValueError, KeyError):
                    continue
                if days >= 1:
                    pending.append({**e, "days_ago": days})
        return pending

    def update_status(self, user_email: str, to_email: str, new_status: str) -> Optional[Dict]:
        for k, v in self._db.items():
            if v.get("from") == user_email and v.get("to") == to_email:
                v["status"] = new_status
                if new_status == "replied":
                    v["replied_at"] = self._now()
                self._save_db()
                return v
        return None

    def get_stats(self, user_email: str) -> Dict:
        emails_list = self._db_get_user_emails(user_email)
        total = len(emails_list)
        sent = sum(1 for e in emails_list if e.get("status") in ("sent", "no_reply"))
        replied = sum(1 for e in emails_list if e.get("status") == "replied")
        bounced = sum(1 for e in emails_list if e.get("status") == "bounced")
        opened = sum(1 for e in emails_list if e.get("opened_count", 0) > 0)
        total_opens = sum(e.get("opened_count", 0) for e in emails_list)
        now = datetime.now()
        pending = sum(1 for e in emails_list if e.get("status") in ("sent", "no_reply")
                      and (now - datetime.strptime(e.get("sent_at", now.strftime("%Y-%m-%d %H:%M")), "%Y-%m-%d %H:%M")).days >= 1)

        return {
            "total": total, "sent": sent, "replied": replied,
            "bounced": bounced, "opened": opened, "pending": pending,
            "open_rate": round(opened / total * 100, 1) if total > 0 else 0,
            "reply_rate": round(replied / total * 100, 1) if total > 0 else 0,
            "total_opens": total_opens,
        }

    def mark_opened(self, tracking_id: str) -> bool:
        for k, v in self._db.items():
            if v.get("tracking_id") == tracking_id:
                v["opened_count"] = v.get("opened_count", 0) + 1
                if not v.get("opened_at"):
                    v["opened_at"] = self._now()
                self._save_db()
                return True
        return False
