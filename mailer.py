"""
SMTP 邮件发送模块 — QQ邮箱 / Gmail / 通用 SMTP
支持发送状态检测、退信识别、发送限制提示
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))


def _get_credentials():
    """优先读 smtp_config.json，其次 .env"""
    from smtp_config import load_config
    cfg = load_config()
    email = cfg.get("smtp_email") or os.getenv("SMTP_EMAIL", "")
    pwd = cfg.get("smtp_password") or os.getenv("SMTP_PASSWORD", "")
    name = cfg.get("sender_name") or os.getenv("SENDER_NAME", "TradeMaster")
    return email, pwd, name


def _is_placeholder(val):
    return not val or "your_email" in val or "your_authorization" in val


def is_configured() -> bool:
    email, pwd, _ = _get_credentials()
    return bool(email and pwd and not _is_placeholder(email) and not _is_placeholder(pwd))


def send_email_smtp(to_email, subject, body, to_name="", from_name=""):
    """
    通过 SMTP 发送邮件。
    返回 dict:
      - success: bool — SMTP 服务器是否接受了邮件
      - delivered: bool | None — None 表示已接受但最终是否送达取决于收件方服务器（异步退信可能）
      - message: str — 用户可读的状态描述
      - detail: str — 技术细节
    """
    email, pwd, sender_name = _get_credentials()

    if not email or not pwd or _is_placeholder(email) or _is_placeholder(pwd):
        return {"success": False, "error": "SMTP 未配置，请在页面设置中填写邮箱信息。点击顶部 ⚙️ 配置"}

    # 构造邮件
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr([from_name or sender_name, email])
    msg["To"] = formataddr([to_name or to_email.split("@")[0], to_email])
    msg["Subject"] = subject
    html_body = body.replace("\n", "<br>")
    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(f"<html><body>{html_body}</body></html>", "html", "utf-8"))

    server = None
    try:
        # 连接
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()

        # 登录
        server.login(email, pwd)

        # 发送 — sendmail 返回被拒收的收件人字典，空字典=全部接受
        refused = server.sendmail(email, [to_email], msg.as_string())
        server.quit()

        if refused:
            # 收件人被 SMTP 服务器当场拒绝
            refused_detail = "; ".join(f"{addr}: {code} {reason}" for addr, (code, reason) in refused.items())
            return {
                "success": False,
                "delivered": False,
                "error": f"邮件被邮件服务器拒绝：{refused_detail[:200]}",
                "hint": "收件人邮箱可能不存在、已停用或设置了拒收规则。请确认邮箱地址有效。"
            }

        # SMTP 服务器接受了邮件，但不能保证送达（异步退信可能）
        return {
            "success": True,
            "delivered": None,  # None = 已接受但无法确定
            "message": f"邮件已被 SMTP 服务器接受，正在投递至 {to_email}",
            "hint": "注意：SMTP 接受 ≠ 最终送达。如收件方服务器拒绝（邮箱不存在、被拦截等），退信通知会发到你的邮箱。请在 QQ邮箱 中留意退信。"
        }

    except smtplib.SMTPAuthenticationError:
        return {
            "success": False, "delivered": False,
            "error": "SMTP 认证失败 — 邮箱地址或授权码不正确",
            "hint": "QQ邮箱需使用授权码（不是QQ密码）。获取方式：QQ邮箱 → 设置 → 账户 → POP3/SMTP服务 → 开启 → 获取授权码"
        }

    except smtplib.SMTPConnectError:
        return {
            "success": False, "delivered": False,
            "error": f"无法连接 {SMTP_SERVER}:{SMTP_PORT}",
            "hint": "请检查网络连接，或尝试切换 SMTP 服务器（QQ邮箱：smtp.qq.com:587，Gmail：smtp.gmail.com:587）"
        }

    except smtplib.SMTPRecipientsRefused as e:
        return {
            "success": False, "delivered": False,
            "error": f"收件人地址被拒：{str(e)[:200]}",
            "hint": "收件人邮箱不存在或拒收了你的邮件。请核实邮箱地址。"
        }

    except smtplib.SMTPSenderRefused as e:
        return {
            "success": False, "delivered": False,
            "error": f"发件人地址被拒：{str(e)[:200]}",
            "hint": "请检查发件人邮箱配置是否正确。"
        }

    except smtplib.SMTPDataError as e:
        return {
            "success": False, "delivered": False,
            "error": f"邮件内容被拒：{str(e)[:200]}",
            "hint": "邮件内容可能触发了反垃圾规则。请精简内容，去掉过多链接或敏感词。"
        }

    except smtplib.SMTPException as e:
        return {
            "success": False, "delivered": False,
            "error": f"SMTP 发送异常：{str(e)[:200]}",
            "hint": "未知 SMTP 错误，请稍后重试或检查邮箱配置。"
        }

    except Exception as e:
        return {
            "success": False, "delivered": False,
            "error": f"发送失败：{str(e)[:200]}"
        }

    finally:
        # 确保连接已关闭
        if server:
            try:
                server.close()
            except Exception:
                pass
