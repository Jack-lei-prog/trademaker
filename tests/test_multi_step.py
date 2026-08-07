# -*- coding: utf-8 -*-
"""多步骤 Agent 编排测试 — detect_intents / get_task_agents / task_plan / 动态迭代上限"""
import pytest
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import detect_intents, get_task_agents, AGENTS


class TestDetectIntents:

    def test_single_keyword_returns_one_agent(self):
        intents = detect_intents("搜索德国蓝牙耳机进口商")
        agent_ids = [a for a, k, p in intents]
        assert "buyer_agent" in agent_ids

    def test_multiple_keywords_returns_multiple_agents(self):
        intents = detect_intents("搜索德国LED进口商并查展会信息")
        agent_ids = [a for a, k, p in intents]
        assert "buyer_agent" in agent_ids
        assert "trade_agent" in agent_ids

    def test_email_keyword_routes_to_email_agent(self):
        intents = detect_intents("给ABC公司写一封开发信")
        agent_ids = [a for a, k, p in intents]
        assert "email_agent" in agent_ids

    def test_no_keyword_returns_coordinator(self):
        intents = detect_intents("今天天气怎么样")
        assert len(intents) == 1
        assert intents[0][0] == "coordinator"

    def test_duplicate_agent_is_deduplicated(self):
        # "搜索" → buyer_agent, "买家" → buyer_agent (same agent, should dedup)
        intents = detect_intents("搜索买家信息")
        agent_ids = [a for a, k, p in intents]
        # buyer_agent appears once, not twice
        assert len(agent_ids) == len(set(agent_ids))

    def test_intents_ordered_by_position(self):
        intents = detect_intents("先搜索进口商，然后写开发信")
        # "搜索" should appear before "开发信"
        buyer_pos = next((p for a, k, p in intents if a == "buyer_agent"), -1)
        email_pos = next((p for a, k, p in intents if a == "email_agent"), -1)
        assert buyer_pos < email_pos

    def test_multi_step_workflow_search_write(self):
        """搜索德国LED进口商→写开发信: 应返回 buyer_agent + email_agent"""
        intents = detect_intents("搜索德国LED进口商并给他们写开发信")
        agent_ids = [a for a, k, p in intents]
        assert "buyer_agent" in agent_ids
        assert "email_agent" in agent_ids
        # buyer_agent 在 email_agent 前面
        assert agent_ids.index("buyer_agent") < agent_ids.index("email_agent")


class TestGetTaskAgents:

    def test_returns_ordered_steps(self):
        tasks = get_task_agents("搜索德国买家并写开发信")
        assert len(tasks) >= 2
        assert tasks[0]["step"] == 1
        assert tasks[1]["step"] == 2

    def test_task_contains_required_fields(self):
        tasks = get_task_agents("搜索LED进口商")
        assert len(tasks) >= 1
        task = tasks[0]
        assert "agent_id" in task
        assert "agent_name" in task
        assert "agent_emoji" in task
        assert "step" in task
        assert "description" in task

    def test_no_intent_returns_coordinator(self):
        tasks = get_task_agents("你好")
        assert len(tasks) == 1
        assert tasks[0]["agent_id"] == "coordinator"

    def test_task_agent_id_is_valid(self):
        tasks = get_task_agents("搜索买家查汇率写开发信")
        for task in tasks:
            assert task["agent_id"] in AGENTS


class TestAgentDefinitions:

    def test_agent_count_is_6(self):
        assert len(AGENTS) == 6

    def test_coordinator_has_empty_tools(self):
        assert AGENTS["coordinator"]["tools"] == []

    def test_buyer_agent_has_search_tools(self):
        tools = AGENTS["buyer_agent"]["tools"]
        assert "search_buyers" in tools
        assert "analyze_company" in tools

    def test_email_agent_has_draft_tools(self):
        tools = AGENTS["email_agent"]["tools"]
        assert "draft_email" in tools
        assert "send_email" in tools
