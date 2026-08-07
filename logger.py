# -*- coding: utf-8 -*-
"""
结构化日志模块 — 含敏感数据自动遮蔽
"""
import logging
import re
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

_logger = None

# ============================================================
# 敏感数据遮蔽规则
# ============================================================

_SENSITIVE_PATTERNS = [
    (r'(Authorization:\s*Bearer\s+)[^\s,]+', r'\1***REDACTED***'),
    (r'(smtp_password[\"\s:=]+)[^\s,"\']+', r'\1***REDACTED***'),
    (r'(password[\"\s:=]+)[^\s,"\']+', r'\1***REDACTED***'),
    (r'(api_key[\"\s:=]+)[^\s,"\']+', r'\1***REDACTED***'),
    (r'(token[\"\s:=]+)[A-Za-z0-9._\-]{20,}', r'\1***REDACTED***'),
    (r'(Bearer\s+)[A-Za-z0-9._\-]{20,}', r'\1***REDACTED***'),
    # 邮箱脱敏：保留 @ 前 2 字符和域名
    (r'([\s:=])([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', r'\1[EMAIL]'),
    # 中文邮箱脱敏
    (r'(邮箱[\s:=]*)([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', r'\1[EMAIL]'),
    # SMTP 邮件正文（body 字段含大段文本时截断）
    (r"('body'[\s:=]+')[\s\S]{100,}(')", r"\1[EMAIL_BODY_TRUNCATED]\2"),
]


def mask_sensitive(text: str) -> str:
    """对字符串中的敏感信息进行遮蔽"""
    if not isinstance(text, str):
        return str(text)
    for pattern, replacement in _SENSITIVE_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


class SensitiveDataFilter(logging.Filter):
    """日志过滤器：自动遮蔽敏感数据"""
    def filter(self, record):
        record.msg = mask_sensitive(str(record.msg))
        if record.args:
            record.args = tuple(mask_sensitive(str(a)) if isinstance(a, str) else a for a in record.args)
        return True


# ============================================================
# Logger 工厂
# ============================================================

def get_logger(name="TradeMaster"):
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger(name)
    _logger.setLevel(logging.INFO)

    # 控制台 handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S"
    ))
    console.addFilter(SensitiveDataFilter())

    # 文件 handler（自动轮转，最大 10MB × 3 个文件）
    file_handler = RotatingFileHandler(
        "trademaster.log", maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    ))
    file_handler.addFilter(SensitiveDataFilter())

    _logger.addHandler(console)
    _logger.addHandler(file_handler)
    return _logger


def log_request(ip: str, method: str, path: str, status: int, duration_ms: float):
    logger = get_logger()
    logger.info(f"REQ {method} {path} | {status} | {duration_ms:.0f}ms | {ip}")


def log_tool_call(tool_name: str, user_email: str, duration_ms: float, success: bool):
    logger = get_logger()
    status = "OK" if success else "FAIL"
    logger.info(f"TOOL {tool_name} | {status} | {duration_ms:.0f}ms | {user_email}")


def log_api_error(endpoint: str, error: str, status: int = 500):
    logger = get_logger()
    logger.error(f"API ERROR {endpoint} | {status} | {error[:200]}")
