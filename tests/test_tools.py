"""测试 tools.py — 工具函数"""
import pytest
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestQueryExchangeRate:
    """汇率查询测试"""

    def test_usd_rate(self):
        from tools import query_exchange_rate
        result = json.loads(query_exchange_rate("USD"))
        assert result["success"] is True
        assert result["currency"] == "USD"
        assert result["rate_to_cny"] > 0

    def test_invalid_currency(self):
        from tools import query_exchange_rate
        result = json.loads(query_exchange_rate("ZZZ"))
        assert result["success"] is False

    def test_lowercase_currency(self):
        from tools import query_exchange_rate
        result = json.loads(query_exchange_rate("eur"))
        assert result["currency"] == "EUR"


class TestSendEmail:
    """邮件生成测试"""

    def test_valid_email(self):
        from tools import send_email
        result = json.loads(send_email("test@example.com", "Subject Line", "Email body"))
        assert result["success"] is True
        assert result["to_email"] == "test@example.com"

    def test_invalid_email(self):
        from tools import send_email
        result = json.loads(send_email("not-an-email", "Subject", "Body"))
        assert result["success"] is False

    def test_subject_extraction(self):
        from tools import send_email
        body = "Subject: Custom Subject\n\nHello, this is the body."
        result = json.loads(send_email("a@b.com", "Fallback Subject", body))
        assert result["subject"] == "Custom Subject"


class TestDraftCustomerReply:
    """客服回复测试"""

    def test_fallback_template(self):
        from tools import draft_customer_reply
        result = draft_customer_reply("我的快递到哪了？", "已发货")
        assert "物流" in result or "发货" in result

    def test_refund_fallback(self):
        from tools import draft_customer_reply
        result = draft_customer_reply("我要退货退款", "已发货")
        assert "退货" in result or "退款" in result or "申请" in result


class TestDailySalesAnalysis:
    """销售分析测试"""

    def test_empty_input(self):
        from tools import analyze_daily_sales
        result = json.loads(analyze_daily_sales(""))
        assert result["total_orders"] == 0
        assert result["total_income"] == 0

    def test_regex_parsing(self):
        from tools import analyze_daily_sales
        result = json.loads(analyze_daily_sales("LED灯 50个 总收入1250元"))
        assert result["total_orders"] == 50
        assert result["total_income"] == 1250

    def test_default_price(self):
        from tools import analyze_daily_sales
        result = json.loads(analyze_daily_sales("蓝牙耳机 10个"))
        assert result["total_orders"] == 10
        assert result["total_income"] == 250  # 默认25元/个


class TestToolFunctionsRegistry:
    """工具注册表测试"""

    def test_all_tools_registered(self):
        from tools import TOOL_FUNCTIONS, TOOL_DESCRIPTIONS
        tool_names = [t["function"]["name"] for t in TOOL_DESCRIPTIONS]
        for name in tool_names:
            assert name in TOOL_FUNCTIONS, f"Tool {name} not in TOOL_FUNCTIONS"

    def test_all_descriptions_have_required_fields(self):
        from tools import TOOL_DESCRIPTIONS
        for t in TOOL_DESCRIPTIONS:
            assert t["type"] == "function"
            assert "function" in t
            assert "name" in t["function"]
            assert "description" in t["function"]
            assert "parameters" in t["function"]


class TestCheckEmailStatus:
    def test_no_file(self):
        from tools import check_email_status
        result = json.loads(check_email_status("noone@test.com"))
        assert result["success"] is True
