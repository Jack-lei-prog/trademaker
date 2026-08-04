"""测试 inquiry_engine.py — 询盘处理引擎"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestExtractClientInfo:
    """客户信息提取测试"""

    def test_extract_email(self):
        from inquiry_engine import extract_client_info
        result = extract_client_info("Hello, I am John from techglobal.com. My email is john@techglobal.com")
        assert result["email"] == "john@techglobal.com"
        assert result["website"] == "techglobal.com"
        assert result["company_name"] == "Techglobal"

    def test_extract_gmail_is_ignored(self):
        from inquiry_engine import extract_client_info
        result = extract_client_info("Contact me at user@gmail.com")
        assert result["email"] == "user@gmail.com"
        # gmail 域名不用于提取公司名
        assert result["company_name"] == ""

    def test_extract_country(self):
        from inquiry_engine import extract_client_info
        result = extract_client_info("We are a company based in Germany looking for suppliers")
        assert result["country"] == "Germany"

    def test_extract_person_name(self):
        from inquiry_engine import extract_client_info
        result = extract_client_info("Dear John Smith, we are interested in your products")
        assert "John" in result["person_name"]

    def test_extract_product_interest(self):
        from inquiry_engine import extract_client_info
        result = extract_client_info("We are interested in LED lights and solar panels.")
        assert "LED" in result["product_interest"] or "lights" in result["product_interest"]

    def test_empty_input(self):
        from inquiry_engine import extract_client_info
        result = extract_client_info("")
        assert result["email"] == ""
        assert result["confidence"] == 0.0

    def test_confidence_scoring(self):
        from inquiry_engine import extract_client_info
        result = extract_client_info(
            "I am Sarah from ABC Corp in UK, interested in bluetooth speakers. "
            "My email is sarah@abccorp.co.uk. Contact me at +44-20-1234-5678"
        )
        # 有 email(3) + company(2) + country(2) + product(2) + name(1) = 10 → 1.0
        assert result["confidence"] >= 0.6


class TestQuickClassify:
    """意图分类降级方案测试"""

    def test_spam_detection(self):
        from inquiry_engine import _quick_classify
        result = _quick_classify("Make money fast!!! Click here to win the lottery!")
        assert result["type"] == "spam"

    def test_genuine_purchase(self):
        from inquiry_engine import _quick_classify
        result = _quick_classify(
            "We are ABC Importers Ltd, interested in 5000 pcs of LED bulbs. "
            "Please send quotation with CE certification."
        )
        assert result["type"] == "genuine_purchase"

    def test_price_shopping(self):
        from inquiry_engine import _quick_classify
        result = _quick_classify("What's your price for bluetooth earphones?")
        assert result["type"] == "price_shopping"


class TestFollowUpQueue:
    """跟进队列测试"""

    def test_add_and_get_pending(self):
        from inquiry_engine import add_to_followup_queue, get_pending_inquiries
        add_to_followup_queue(
            user_email="test@test.com",
            client_email="client@test.com",
            client_name="Test Client",
            subject="Test Inquiry",
            inquiry_text="I want to buy 1000 pcs",
            intent_type="genuine_purchase",
        )
        pending = get_pending_inquiries("test@test.com")
        assert len(pending) >= 1
        assert pending[-1]["client_email"] == "client@test.com"

    def test_mark_replied(self):
        from inquiry_engine import add_to_followup_queue, get_pending_inquiries, mark_inquiry_replied
        fuid = add_to_followup_queue(
            user_email="test2@test.com",
            client_email="client2@test.com",
            subject="Test",
            inquiry_text="Test",
            intent_type="genuine_purchase",
        )
        mark_inquiry_replied(fuid)
        pending = get_pending_inquiries("test2@test.com")
        assert not any(p["id"] == fuid for p in pending)
