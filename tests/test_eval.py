"""
Unit tests for automated evaluator benchmarks.
"""

import unittest
from src.eval.evaluator import evaluator


class TestEval(unittest.TestCase):

    def test_evaluator_scoring(self):
        eval_res = evaluator.evaluate_response(
            query="Analyze GOOGL stock risk",
            response_text="Executive Briefing for GOOGL stock risk showing LOW risk.",
            tools_called=["fetch_market_data", "calculate_risk_and_financial_health", "generate_executive_briefing"],
            expected_tools=["fetch_market_data", "generate_executive_briefing"],
            context_used=True,
            latency_ms=250.0
        )

        self.assertGreaterEqual(eval_res.overall_score, 90.0)
        self.assertEqual(eval_res.tool_usage_score, 25.0)
        self.assertEqual(eval_res.relevance_score, 25.0)
        self.assertEqual(eval_res.memory_context_score, 20.0)
        self.assertEqual(eval_res.latency_score, 15.0)


if __name__ == "__main__":
    unittest.main()
