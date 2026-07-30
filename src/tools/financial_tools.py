"""
Financial Analytics & Risk Tools for Google ADK Agent.
Implements financial modeling, risk score calculation, and executive report formatting.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class RiskAssessmentInput(BaseModel):
    revenue_growth_pct: float = Field(description="Annual revenue growth percentage (e.g. 15.5 for 15.5%)")
    gross_margin_pct: float = Field(description="Gross margin percentage (e.g. 65.0 for 65%)")
    debt_to_equity: float = Field(description="Debt-to-Equity ratio (e.g. 0.8)")
    market_volatility: float = Field(default=0.20, description="Annualized stock price volatility (0.0 to 1.0)")


class RiskAssessmentOutput(BaseModel):
    risk_score: float = Field(description="Composite risk score from 0.0 (Low Risk) to 100.0 (High Risk)")
    risk_level: str = Field(description="Risk classification: LOW, MODERATE, HIGH, CRITICAL")
    financial_health_rating: str = Field(description="Rating: AAA, AA, A, BBB, BB, B")
    key_vulnerabilities: List[str]
    strategic_recommendations: List[str]


def calculate_risk_and_financial_health(
    revenue_growth_pct: float,
    gross_margin_pct: float,
    debt_to_equity: float,
    market_volatility: float = 0.20
) -> Dict[str, Any]:
    """
    Computes a composite enterprise risk score and financial health classification based on fundamental ratios.

    Args:
        revenue_growth_pct: Year-over-year revenue growth percentage.
        gross_margin_pct: Gross profit margin percentage.
        debt_to_equity: Debt to equity ratio.
        market_volatility: Volatility score (0.0 to 1.0). Default is 0.20.

    Returns:
        Structured risk assessment object containing risk score, risk level, rating, and strategic advice.
    """
    # Base risk starts at 50
    risk = 50.0

    # Growth impact
    if revenue_growth_pct > 20.0:
        risk -= 15.0
    elif revenue_growth_pct > 5.0:
        risk -= 5.0
    else:
        risk += 15.0

    # Gross margin impact
    if gross_margin_pct > 60.0:
        risk -= 15.0
    elif gross_margin_pct < 30.0:
        risk += 15.0

    # Debt ratio impact
    if debt_to_equity > 2.0:
        risk += 20.0
    elif debt_to_equity < 0.5:
        risk -= 10.0

    # Volatility impact
    risk += market_volatility * 25.0

    # Clamp risk score between 0 and 100
    risk_score = round(max(5.0, min(95.0, risk)), 1)

    if risk_score < 30.0:
        risk_level = "LOW"
        rating = "AAA"
    elif risk_score < 50.0:
        risk_level = "MODERATE"
        rating = "AA"
    elif risk_score < 70.0:
        risk_level = "HIGH"
        rating = "BBB"
    else:
        risk_level = "CRITICAL"
        rating = "B"

    vulnerabilities = []
    if debt_to_equity > 1.5:
        vulnerabilities.append("Elevated leverage relative to equity base.")
    if revenue_growth_pct < 5.0:
        vulnerabilities.append("Slow revenue growth trajectory.")
    if gross_margin_pct < 40.0:
        vulnerabilities.append("Margin compression exposure.")
    if not vulnerabilities:
        vulnerabilities.append("No critical balance sheet vulnerabilities identified.")

    recommendations = [
        "Maintain adequate cash reserves to cushion macro volatility.",
        "Focus capital deployment on high-margin product segments."
    ]
    if debt_to_equity > 1.5:
        recommendations.append("Prioritize debt reduction and refinancing terms.")

    output = RiskAssessmentOutput(
        risk_score=risk_score,
        risk_level=risk_level,
        financial_health_rating=rating,
        key_vulnerabilities=vulnerabilities,
        strategic_recommendations=recommendations
    )
    return output.model_dump()


def generate_executive_briefing(
    company_or_topic: str,
    key_findings: List[str],
    risk_rating: str = "MODERATE",
    action_items: List[str] = None
) -> Dict[str, Any]:
    """
    Formats multi-agent research findings into a standardized C-suite Executive Briefing structure.

    Args:
        company_or_topic: Name of target company, sector, or market topic.
        key_findings: List of key analytical findings extracted by sub-agents.
        risk_rating: Composite risk rating ('LOW', 'MODERATE', 'HIGH').
        action_items: Recommended executive action items.

    Returns:
        Structured executive briefing artifact ready for distribution.
    """
    if action_items is None:
        action_items = ["Schedule quarterly review with strategy committee.", "Monitor competitor pricing shifts."]

    return {
        "title": f"Executive Intelligence Briefing: {company_or_topic}",
        "status": "APPROVED",
        "composite_risk_rating": risk_rating,
        "executive_summary": f"This briefing synthesizes real-time market data, quantitative health metrics, and strategic risk indicators for {company_or_topic}.",
        "key_findings": key_findings,
        "strategic_action_items": action_items,
        "disclaimer": "Generated autonomously by ADK Market Intelligence Agent System."
    }
