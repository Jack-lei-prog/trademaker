"""
结构化日志模块
"""
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

_logger = None


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

    # 文件 handler（自动轮转，最大 10MB × 3 个文件）
    file_handler = RotatingFileHandler(
        "trademaster.log", maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    ))

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
