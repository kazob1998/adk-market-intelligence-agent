"""
Integration tests for ADK Multi-Agent Workflow Execution.
"""

import unittest
from src.agent import workflow_executor, root_agent


class TestAgent(unittest.TestCase):

    def test_root_agent_initialization(self):
        self.assertEqual(root_agent.name, "CoordinatorAgent")
        self.assertEqual(len(root_agent.sub_agents), 3)
        self.assertEqual(len(root_agent.tools), 4)

    def test_workflow_execution(self):
        res = workflow_executor.run_intelligence_workflow(
            query="Analyze Alphabet (GOOGL) financial risk and market outlook",
            session_id="test_workflow_session"
        )

        self.assertIn("executive_briefing", res)
        self.assertEqual(res["ticker"], "GOOGL")
        self.assertGreater(len(res["tools_executed"]), 0)
        self.assertGreater(res["latency_ms"], 0)


if __name__ == "__main__":
    unittest.main()
