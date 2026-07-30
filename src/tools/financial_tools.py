"""
Financial Analytics & Risk Tools for Google ADK Agent.
Implements strongly-typed financial modeling tools utilizing explicit Pydantic input schemas,
validated Pydantic output models, and guided error handling with LLM recovery instructions.
"""

from typing import List, Dict, Any, Optional, Union
from src.compat import BaseModel, Field, ValidationError


class RiskAssessmentInput(BaseModel):
    """Explicit Pydantic Input Schema for Financial Health & Risk Assessment."""
    revenue_growth_pct: float = Field(
        description="Annual revenue growth percentage (e.g. 15.5 for 15.5%, -5.0 for -5.0%)",
        ge=-100.0,
        le=500.0
    )
    gross_margin_pct: float = Field(
        description="Gross margin percentage (e.g. 65.0 for 65.0%)",
        ge=0.0,
        le=100.0
    )
    debt_to_equity: float = Field(
        description="Debt-to-Equity ratio (e.g. 0.4 for low debt, 2.5 for high leverage)",
        ge=0.0,
        le=50.0
    )
    market_volatility: float = Field(
        default=0.20,
        description="Annualized stock price volatility (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )


class ExecutiveBriefingRequest(BaseModel):
    """Explicit Pydantic Input Schema for Executive Briefing generation."""
    company_or_topic: str = Field(
        description="Target company name, ticker, or strategic topic (e.g. 'GOOGL', 'Enterprise AI')",
        min_length=1
    )
    key_findings: List[str] = Field(
        default_factory=list,
        description="List of key analytical findings extracted by sub-agents"
    )
    risk_rating: str = Field(
        default="MODERATE",
        description="Composite risk rating: 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'"
    )
    action_items: Optional[List[str]] = Field(
        default=None,
        description="Recommended executive action items"
    )


class FinancialToolErrorResponse(BaseModel):
    """Guided Error Response schema with actionable recovery instructions for financial models."""
    status: str = "error"
    error_code: str
    error_message: str
    recovery_instructions: str
    suggested_fix: Dict[str, Any]


class RiskAssessmentOutput(BaseModel):
    risk_score: float = Field(description="Composite risk score from 0.0 (Low Risk) to 100.0 (High Risk)")
    risk_level: str = Field(description="Risk classification: LOW, MODERATE, HIGH, CRITICAL")
    financial_health_rating: str = Field(description="Rating: AAA, AA, A, BBB, BB, B")
    key_vulnerabilities: List[str]
    strategic_recommendations: List[str]


class ExecutiveBriefingResponse(BaseModel):
    title: str
    status: str
    composite_risk_rating: str
    executive_summary: str
    key_findings: List[str]
    strategic_action_items: List[str]
    disclaimer: str


def calculate_risk_and_financial_health(
    request: Optional[RiskAssessmentInput] = None,
    *,
    revenue_growth_pct: Optional[float] = None,
    gross_margin_pct: Optional[float] = None,
    debt_to_equity: Optional[float] = None,
    market_volatility: Optional[float] = 0.20
) -> Dict[str, Any]:
    """
    Computes a composite enterprise risk score and financial health classification based on fundamental ratios.

    Args:
        request: Explicit Pydantic RiskAssessmentInput schema instance.
        revenue_growth_pct: Year-over-year revenue growth percentage.
        gross_margin_pct: Gross profit margin percentage (0 to 100).
        debt_to_equity: Debt to equity ratio (>= 0).
        market_volatility: Volatility score (0.0 to 1.0). Default is 0.20.

    Returns:
        Structured RiskAssessmentOutput dictionary or guided FinancialToolErrorResponse.
    """
    # 1. Resolve and Validate Input via Pydantic Schema
    try:
        if request is not None:
            validated_req = request
        else:
            if revenue_growth_pct is None or gross_margin_pct is None or debt_to_equity is None:
                return FinancialToolErrorResponse(
                    error_code="MISSING_REQUIRED_FINANCIAL_METRICS",
                    error_message="Missing required parameters: revenue_growth_pct, gross_margin_pct, and debt_to_equity must be provided.",
                    recovery_instructions=(
                        "Provide all three core metrics: revenue_growth_pct (e.g. 15.0), "
                        "gross_margin_pct (e.g. 55.0), and debt_to_equity (e.g. 0.5)."
                    ),
                    suggested_fix={
                        "revenue_growth_pct": 14.5,
                        "gross_margin_pct": 58.2,
                        "debt_to_equity": 0.4,
                        "market_volatility": 0.20
                    }
                ).model_dump()

            validated_req = RiskAssessmentInput(
                revenue_growth_pct=revenue_growth_pct,
                gross_margin_pct=gross_margin_pct,
                debt_to_equity=debt_to_equity,
                market_volatility=market_volatility if market_volatility is not None else 0.20
            )
    except ValidationError as ve:
        return FinancialToolErrorResponse(
            error_code="VALIDATION_ERROR",
            error_message=f"Financial parameters out of bounds: {str(ve.errors())}",
            recovery_instructions=(
                "Ensure gross_margin_pct is between 0 and 100, debt_to_equity is non-negative, "
                "and market_volatility is between 0.0 and 1.0."
            ),
            suggested_fix={
                "revenue_growth_pct": 15.0,
                "gross_margin_pct": 60.0,
                "debt_to_equity": 0.5,
                "market_volatility": 0.20
            }
        ).model_dump()
    except Exception as e:
        return FinancialToolErrorResponse(
            error_code="UNEXPECTED_INPUT_ERROR",
            error_message=str(e),
            recovery_instructions="Pass valid numeric values conforming to RiskAssessmentInput schema.",
            suggested_fix={
                "revenue_growth_pct": 15.0,
                "gross_margin_pct": 60.0,
                "debt_to_equity": 0.5
            }
        ).model_dump()

    # 2. Risk Calculation Logic
    risk = 50.0

    # Growth impact
    if validated_req.revenue_growth_pct > 20.0:
        risk -= 15.0
    elif validated_req.revenue_growth_pct > 5.0:
        risk -= 5.0
    else:
        risk += 15.0

    # Gross margin impact
    if validated_req.gross_margin_pct > 60.0:
        risk -= 15.0
    elif validated_req.gross_margin_pct < 30.0:
        risk += 15.0

    # Debt ratio impact
    if validated_req.debt_to_equity > 2.0:
        risk += 20.0
    elif validated_req.debt_to_equity < 0.5:
        risk -= 10.0

    # Volatility impact
    risk += validated_req.market_volatility * 25.0

    # Clamp risk score between 5 and 95
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
    if validated_req.debt_to_equity > 1.5:
        vulnerabilities.append("Elevated leverage relative to equity base.")
    if validated_req.revenue_growth_pct < 5.0:
        vulnerabilities.append("Slow revenue growth trajectory.")
    if validated_req.gross_margin_pct < 40.0:
        vulnerabilities.append("Margin compression exposure.")
    if not vulnerabilities:
        vulnerabilities.append("No critical balance sheet vulnerabilities identified.")

    recommendations = [
        "Maintain adequate cash reserves to cushion macro volatility.",
        "Focus capital deployment on high-margin product segments."
    ]
    if validated_req.debt_to_equity > 1.5:
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
    request: Optional[ExecutiveBriefingRequest] = None,
    *,
    company_or_topic: Optional[str] = None,
    key_findings: Optional[List[str]] = None,
    risk_rating: Optional[str] = "MODERATE",
    action_items: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Formats multi-agent research findings into a standardized C-suite Executive Briefing structure.

    Args:
        request: Explicit Pydantic ExecutiveBriefingRequest schema instance.
        company_or_topic: Name of target company, sector, or market topic.
        key_findings: List of key analytical findings extracted by sub-agents.
        risk_rating: Composite risk rating ('LOW', 'MODERATE', 'HIGH', 'CRITICAL').
        action_items: Recommended executive action items.

    Returns:
        Structured ExecutiveBriefingResponse dictionary or guided error response.
    """
    # 1. Resolve and Validate Input via Pydantic Schema
    try:
        if request is not None:
            validated_req = request
        else:
            validated_req = ExecutiveBriefingRequest(
                company_or_topic=company_or_topic or "Enterprise Sector",
                key_findings=key_findings or [],
                risk_rating=risk_rating or "MODERATE",
                action_items=action_items
            )
    except ValidationError as ve:
        return FinancialToolErrorResponse(
            error_code="VALIDATION_ERROR",
            error_message=f"Briefing request validation failed: {str(ve.errors())}",
            recovery_instructions="Provide a valid 'company_or_topic' string and findings list.",
            suggested_fix={"company_or_topic": "GOOGL", "risk_rating": "LOW"}
        ).model_dump()
    except Exception as e:
        return FinancialToolErrorResponse(
            error_code="UNEXPECTED_INPUT_ERROR",
            error_message=str(e),
            recovery_instructions="Pass arguments matching the ExecutiveBriefingRequest Pydantic model.",
            suggested_fix={"company_or_topic": "GOOGL"}
        ).model_dump()

    actions = validated_req.action_items or [
        "Capitalize on high-margin product growth opportunities.",
        "Maintain continuous observability over quantitative risk metrics.",
        "Review strategic asset allocation on a quarterly cadence."
    ]

    response = ExecutiveBriefingResponse(
        title=f"Executive Intelligence Briefing: {validated_req.company_or_topic}",
        status="APPROVED",
        composite_risk_rating=validated_req.risk_rating.upper(),
        executive_summary=(
            f"This briefing synthesizes real-time market data, quantitative health metrics, "
            f"and strategic risk indicators for {validated_req.company_or_topic}."
        ),
        key_findings=validated_req.key_findings,
        strategic_action_items=actions,
        disclaimer="Generated autonomously by ADK Market Intelligence Agent System. For analytical research only."
    )
    return response.model_dump()
