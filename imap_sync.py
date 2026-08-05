"""
IMAP 收件箱同步 — 自动检测客户回复
支持 QQ邮箱 / Gmail / 通用 IMAP
"""
import imaplib
import email
import re
import os
from datetime import datetime, timedelta
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()


def _get_imap_config():
    """获取 IMAP 配置"""
    from smtp_config import load_config
    cfg = load_config()
    email_addr = cfg.get("smtp_email") or os.getenv("SMTP_EMAIL", "")
    pwd = cfg.get("smtp_password") or os.getenv("SMTP_PASSWORD", "")

    if not email_addr or not pwd:
        return None

    # 根据邮箱自动选择 IMAP 服务器
    domain = email_addr.split("@")[1].lower() if "@" in email_addr else ""
    servers = {
        "qq.com": ("imap.qq.com", 993),
        "gmail.com": ("imap.gmail.com", 993),
        "163.com": ("imap.163.com", 993),
        "126.com": ("imap.126.com", 993),
        "outlook.com": ("outlook.office365.com", 993),
    }
    server, port = servers.get(domain, ("imap.qq.com", 993))
    return {"email": email_addr, "password": pwd, "server": server, "port": port}


def is_imap_configured() -> bool:
    cfg = _get_imap_config()
    return cfg is not None and cfg["email"] and cfg["password"]


def _decode_header_val(val):
    """解码邮件头"""
    if val is None:
        return ""
    decoded_parts = decode_header(val)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or "utf-8", errors="replace"))
            except Exception:
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(str(part))
    return "".join(result)


def _extract_email(from_addr: str) -> str:
    """从 From 地址提取邮箱"""
    match = re.search(r'[\w.+-]+@[\w.-]+', from_addr)
    return match.group(0).lower() if match else ""


def check_replies(user_email: str = "") -> list:
    """
    检查收件箱中的新回复。
    返回：匹配到的回复列表
    """
    cfg = _get_imap_config()
    if not cfg:
        return []

    try:
        # 连接 IMAP
        mail = imaplib.IMAP4_SSL(cfg["server"], cfg["port"], timeout=15)
        mail.login(cfg["email"], cfg["password"])
        mail.select("INBOX")

        # 搜索最近14天的邮件
        since_date = (datetime.now() - timedelta(days=14)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE {since_date})')

        if status != "OK" or not messages or not messages[0]:
            # 降级：搜索所有邮件（最多取最近50封）
            status, messages = mail.search(None, 'ALL')
            if status != "OK":
                mail.logout()
                return []

        # 获取所有已发送邮件的收件人列表（不限制user_email，全面匹配）
        from email_providers.local import LocalEmailProvider
        provider = LocalEmailProvider()
        all_data = provider._load()
        all_sent = list(all_data.values())
        # Build sent_to set from ALL emails in the system
        sent_to = set()
        for e in all_sent:
            to_addr = (e.get("to") or "").lower()
            if to_addr:
                sent_to.add(to_addr)
        sent_emails = all_sent  # Keep full records for matching

        if not sent_to:
            mail.logout()
            return [{"note": f"未找到已发送邮件记录（user_email={user_email}, smtp={cfg['email']}）。请检查发送邮件时使用的账号。"}]

        new_replies = []
        msg_ids = []
        raw = messages[0] if messages else b''
        if raw:
            ids_str = raw.decode() if isinstance(raw, bytes) else raw
            msg_ids = ids_str.split()

        # 只检查最近50封
        for msg_id in msg_ids[-50:]:
            try:
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                from_addr = _decode_header_val(msg.get("From", ""))
                from_email = _extract_email(from_addr)
                subject = _decode_header_val(msg.get("Subject", ""))
                date_str = msg.get("Date", "")

                # 检查是否是我们发过邮件的人回复的
                if from_email in sent_to:
                    # 找到对应的已发送邮件
                    for e in sent_emails:
                        if e.get("to", "").lower() == from_email and e.get("status") in ("sent", "no_reply"):
                            # 提取正文
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    ctype = part.get_content_type()
                                    if ctype == "text/plain":
                                        try:
                                            body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                                        except Exception:
                                            pass
                                        break
                            else:
                                try:
                                    body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
                                except Exception:
                                    pass

                            # 更新所有匹配记录的状态（不管 user_email 标识）
                            all_data = provider._load()
                            for eid, record in all_data.items():
                                if record.get("to", "").lower() == from_email:
                                    record["status"] = "replied"
                                    record["replied_at"] = provider._now()
                            provider._save(all_data)

                            # AI 意图分类
                            from email_tracker import classify_intent
                            intent = classify_intent(body[:500] if body else "回复", subject)

                            new_replies.append({
                                "from": from_addr,
                                "from_email": from_email,
                                "subject": subject,
                                "date": date_str,
                                "body_preview": (body or "")[:200],
                                "intent": intent.get("intent", ""),
                                "intent_brief": intent.get("brief", ""),
                                "original_subject": e.get("subject", ""),
                            })
                            break

            except Exception:
                continue

        mail.logout()
        return new_replies

    except imaplib.IMAP4.error as e:
        print(f"[IMAP] Login failed: {e}")
        return []
    except Exception as e:
        print(f"[IMAP] Error: {e}")
        return []
