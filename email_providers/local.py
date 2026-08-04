# -*- coding: utf-8 -*-
"""
本地邮件后端 — 基于 SQLite KV 存储
支持 tracking_id、opened_at 字段，支持打开追踪
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from . import BaseEmailProvider


class LocalEmailProvider(BaseEmailProvider):
    def __init__(self, file_path="emails_sent.json"):
        self._kv_key = "emails_sent"

    def _load(self) -> dict:
        import db
        data = db.kv_get(self._kv_key)
        if data is not None:
            return data
        # 首次从 JSON 文件迁移
        if os.path.exists("emails_sent.json"):
            try:
                with open("emails_sent.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                db.kv_set(self._kv_key, data)
                return data
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _save(self, data: dict):
        import db
        db.kv_set(self._kv_key, data)

    def record_sent(self, user_email: str, to_email: str, to_name: str,
                    subject: str, body: str, tracking_id: str = "") -> str:
        now = self._now()
        eid = f"{user_email}_{to_email}_{now.replace(' ', '_').replace(':', '-')}"
        emails = self._load()
        emails[eid] = {
            "id": eid,
            "from": user_email,
            "to": to_email,
            "to_name": to_name,
            "subject": subject,
            "body_preview": body[:200],
            "sent_at": now,
            "status": "sent",
            "followups": [],
            "tracking_id": tracking_id,
            "opened_at": "",
            "opened_count": 0,
            "replied_at": "",
            "intent": "",
        }
        self._save(emails)
        return eid

    def get_user_emails(self, user_email: str) -> List[Dict]:
        return [v for v in self._load().values() if v.get("from") == user_email]

    def get_pending_followups(self, user_email: str) -> List[Dict]:
        now = datetime.now()
        pending = []
        for e in self.get_user_emails(user_email):
            if e.get("status") in ("sent", "no_reply"):
                days = (now - datetime.strptime(e["sent_at"], "%Y-%m-%d %H:%M")).days
                if days >= 1:
                    pending.append({**e, "days_ago": days})
        return pending

    def update_status(self, user_email: str, to_email: str, new_status: str) -> Optional[Dict]:
        emails = self._load()
        for k, v in emails.items():
            if v.get("from") == user_email and v.get("to") == to_email:
                v["status"] = new_status
                if new_status == "replied":
                    v["replied_at"] = self._now()
                self._save(emails)
                return v
        return None

    def sync_inbox(self, user_email: str) -> List[Dict]:
        return []

    def get_stats(self, user_email: str) -> Dict:
        emails_list = self.get_user_emails(user_email)
        total = len(emails_list)
        sent = sum(1 for e in emails_list if e.get("status") in ("sent", "no_reply"))
        replied = sum(1 for e in emails_list if e.get("status") == "replied")
        bounced = sum(1 for e in emails_list if e.get("status") == "bounced")
        opened = sum(1 for e in emails_list if e.get("opened_count", 0) > 0)
        pending = sum(1 for e in emails_list if e.get("status") in ("sent", "no_reply")
                      and (datetime.now() - datetime.strptime(e["sent_at"], "%Y-%m-%d %H:%M")).days >= 1)

        dates = {}
        for e in emails_list:
            d = e.get("sent_at", "")[:10]
            dates[d] = dates.get(d, 0) + 1

        return {
            "total": total,
            "sent": sent,
            "replied": replied,
            "bounced": bounced,
            "opened": opened,
            "pending": pending,
            "open_rate": round(opened / total * 100, 1) if total > 0 else 0,
            "reply_rate": round(replied / total * 100, 1) if total > 0 else 0,
            "daily_sends": dates,
        }

    def mark_opened(self, tracking_id: str) -> bool:
        emails = self._load()
        for k, v in emails.items():
            if v.get("tracking_id") == tracking_id:
                v["opened_count"] = v.get("opened_count", 0) + 1
                if not v.get("opened_at"):
                    v["opened_at"] = self._now()
                self._save(emails)
                return True
        return False
