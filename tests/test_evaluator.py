"""测试 evaluator.py — GAN 评价系统"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHeuristicEvaluate:
    """启发式评价测试"""

    def test_returns_all_fields(self):
        from evaluator import heuristic_evaluate
        result = heuristic_evaluate("搜索电子产品买家", "这是1家买家：Apple Inc. contact@apple.com")
        assert "scores" in result
        assert "strengths" in result
        assert "weaknesses" in result
        assert "suggestion" in result
        assert "need_improve" in result

    def test_relevance_scoring(self):
        from evaluator import heuristic_evaluate
        result = heuristic_evaluate("查询美元汇率", "1 USD = 7.25 CNY")
        assert result["scores"]["relevance"] >= 7

    def test_completeness_email(self):
        from evaluator import heuristic_evaluate
        result = heuristic_evaluate("写一封开发信",
            "Subject: Cooperation\nDear Sir,\nWe offer LED lights.\nBest regards,\nSales")
        assert result["scores"]["completeness"] >= 2  # 至少有 subject + dear + regards

    def test_irrelevant_answer(self):
        from evaluator import heuristic_evaluate
        result = heuristic_evaluate("搜索买家", "今天天气很好")
        assert result["scores"]["relevance"] < 7

    def test_scores_in_range(self):
        from evaluator import heuristic_evaluate
        result = heuristic_evaluate("测试问题", "测试回答内容")
        for key, val in result["scores"].items():
            assert 0 <= val <= 10, f"Score {key}={val} out of range"

    def test_need_improve_flag(self):
        from evaluator import heuristic_evaluate
        good = heuristic_evaluate("写开发信给ABC公司推LED灯",
            "Subject: LED Lights Offer\n\nDear ABC Team,\n\n"
            "We are a professional LED manufacturer. Our products feature CE and RoHS certification.\n"
            "Please contact us at sales@led.com for quotation.\n\nBest regards,\nSales Team")
        poor = heuristic_evaluate("复杂问题", "短回答")
        # 好回答不应该需要改进（或至少分数更高）
        assert good["scores"]["overall"] > poor["scores"]["overall"]


class TestDualEvaluate:
    def test_returns_heuristic_and_kimi(self):
        from evaluator import dual_evaluate
        result = dual_evaluate("测试", "回答")
        assert "heuristic" in result
        assert "kimi" in result
        assert "scores" in result["heuristic"]
