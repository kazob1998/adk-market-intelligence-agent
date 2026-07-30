"""
Unit tests for custom market and financial tools.
"""

import unittest
from src.tools.market_tools import fetch_market_data, search_industry_news
from src.tools.financial_tools import calculate_risk_and_financial_health, generate_executive_briefing


class TestTools(unittest.TestCase):

    def test_fetch_market_data_valid_ticker(self):
        res = fetch_market_data(ticker="GOOGL", timeframe="1M")
        self.assertEqual(res["ticker"], "GOOGL")
        self.assertEqual(res["company_name"], "Alphabet Inc.")
        self.assertIn("current_price", res)
        self.assertEqual(res["currency"], "USD")

    def test_search_industry_news(self):
        res = search_industry_news(query="AI Agents", category="tech", max_results=2)
        self.assertEqual(res["query"], "AI Agents")
        self.assertLessEqual(len(res["articles"]), 2)
        self.assertIn("headline", res["articles"][0])

    def test_calculate_risk_and_financial_health(self):
        res = calculate_risk_and_financial_health(
            revenue_growth_pct=25.0,
            gross_margin_pct=70.0,
            debt_to_equity=0.3
        )
        self.assertIn("risk_score", res)
        self.assertIn(res["risk_level"], ["LOW", "MODERATE", "HIGH", "CRITICAL"])
        self.assertEqual(res["financial_health_rating"], "AAA")

    def test_generate_executive_briefing(self):
        res = generate_executive_briefing(
            company_or_topic="GOOGL",
            key_findings=["Strong Q3 ad growth", "Cloud margin expansion"],
            risk_rating="LOW"
        )
        self.assertEqual(res["status"], "APPROVED")
        self.assertEqual(res["composite_risk_rating"], "LOW")
        self.assertEqual(len(res["key_findings"]), 2)


if __name__ == "__main__":
    unittest.main()
