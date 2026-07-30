"""
Unit tests for custom market and financial tools, verifying Pydantic schema validation
and guided error recovery instructions for LLMs.
"""

import unittest
from src.tools.market_tools import (
    fetch_market_data,
    search_industry_news,
    MarketDataRequest,
    NewsSearchRequest
)
from src.tools.financial_tools import (
    calculate_risk_and_financial_health,
    generate_executive_briefing,
    RiskAssessmentInput,
    ExecutiveBriefingRequest
)


class TestTools(unittest.TestCase):

    def test_fetch_market_data_direct_pydantic_schema(self):
        # Explicit Pydantic input model
        req = MarketDataRequest(ticker="GOOGL", timeframe="1M")
        res = fetch_market_data(request=req)

        self.assertEqual(res["ticker"], "GOOGL")
        self.assertEqual(res["company_name"], "Alphabet Inc.")
        self.assertIn("current_price", res)
        self.assertEqual(res["currency"], "USD")
        self.assertEqual(res["timeframe"], "1M")

    def test_fetch_market_data_guided_error_handling(self):
        # Test invalid ticker
        res = fetch_market_data(ticker="INVALID$$$TICKER_TOO_LONG_12345")
        self.assertEqual(res.get("status"), "error")
        self.assertIn("recovery_instructions", res)
        self.assertIn("suggested_fix", res)

    def test_search_industry_news_direct_pydantic_schema(self):
        req = NewsSearchRequest(query="AI Agents", category="tech", max_results=2)
        res = search_industry_news(request=req)

        self.assertEqual(res["query"], "AI Agents")
        self.assertLessEqual(len(res["articles"]), 2)
        self.assertIn("headline", res["articles"][0])

    def test_calculate_risk_direct_pydantic_schema(self):
        req = RiskAssessmentInput(
            revenue_growth_pct=25.0,
            gross_margin_pct=70.0,
            debt_to_equity=0.3,
            market_volatility=0.20
        )
        res = calculate_risk_and_financial_health(request=req)

        self.assertIn("risk_score", res)
        self.assertIn(res["risk_level"], ["LOW", "MODERATE", "HIGH", "CRITICAL"])
        self.assertEqual(res["financial_health_rating"], "AAA")

    def test_calculate_risk_guided_error_handling(self):
        # Negative gross margin validation error
        res = calculate_risk_and_financial_health(
            revenue_growth_pct=10.0,
            gross_margin_pct=-20.0,
            debt_to_equity=0.5
        )
        self.assertEqual(res.get("status"), "error")
        self.assertIn("recovery_instructions", res)
        self.assertIn("suggested_fix", res)

    def test_generate_executive_briefing_direct_pydantic_schema(self):
        req = ExecutiveBriefingRequest(
            company_or_topic="GOOGL",
            key_findings=["Strong Q3 ad growth", "Cloud margin expansion"],
            risk_rating="LOW"
        )
        res = generate_executive_briefing(request=req)

        self.assertEqual(res["status"], "APPROVED")
        self.assertEqual(res["composite_risk_rating"], "LOW")
        self.assertEqual(len(res["key_findings"]), 2)
        self.assertIn("disclaimer", res)


if __name__ == "__main__":
    unittest.main()
