"""
Market Research Tools for Google ADK Agent.
Implements strongly-typed tool interfaces utilizing explicit Pydantic input schemas,
validated Pydantic output models, and guided error handling with LLM recovery instructions.
"""

from typing import List, Optional, Dict, Any, Union
from src.compat import BaseModel, Field, ValidationError
import datetime
import re


class MarketDataRequest(BaseModel):
    """Explicit Pydantic Input Schema for Market Data retrieval."""
    ticker: str = Field(
        description="Stock ticker symbol (1-5 alphanumeric chars, e.g. GOOGL, NVDA, AAPL, MSFT)",
        min_length=1,
        max_length=10
    )
    timeframe: str = Field(
        default="1M",
        description="Analysis lookback window. Allowed values: '1D', '1W', '1M', '3M', '1Y', '5Y'"
    )


class NewsSearchRequest(BaseModel):
    """Explicit Pydantic Input Schema for Industry News search."""
    query: str = Field(
        description="Company name or sector research topic (e.g. 'Cloud AI', 'NVIDIA')",
        min_length=1
    )
    category: str = Field(
        default="general",
        description="News category: 'tech', 'finance', 'regulatory', 'general'"
    )
    max_results: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of articles to return (1-10)"
    )


class ToolErrorResponse(BaseModel):
    """Guided Error Response schema providing actionable recovery instructions to LLMs."""
    status: str = "error"
    error_code: str
    error_message: str
    recovery_instructions: str
    suggested_fix: Dict[str, Any]


class MarketNewsItem(BaseModel):
    headline: str
    source: str
    published_date: str
    summary: str
    relevance_score: float


class NewsSearchResponse(BaseModel):
    query: str
    category: str
    total_results: int
    articles: List[MarketNewsItem]


class MarketDataResponse(BaseModel):
    ticker: str
    company_name: str
    current_price: float
    currency: str
    percent_change_30d: float
    market_cap: str
    pe_ratio: float
    analyst_consensus: str
    key_drivers: List[str]
    timeframe: str = "1M"


def fetch_market_data(
    request: Optional[MarketDataRequest] = None,
    *,
    ticker: Optional[str] = None,
    timeframe: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetches real-time market data, valuation metrics, and stock performance for a given ticker.

    Args:
        request: Explicit Pydantic MarketDataRequest schema instance.
        ticker: Optional keyword ticker string if called directly.
        timeframe: Optional lookback timeframe ('1D', '1W', '1M', '3M', '1Y').

    Returns:
        Validated MarketDataResponse dictionary or guided ToolErrorResponse with recovery steps.
    """
    # 1. Resolve and Validate Input via Pydantic Schema
    try:
        if request is not None:
            validated_req = request
        else:
            validated_req = MarketDataRequest(
                ticker=ticker or "",
                timeframe=timeframe or "1M"
            )
    except ValidationError as ve:
        return ToolErrorResponse(
            error_code="VALIDATION_ERROR",
            error_message=f"Input validation failed: {str(ve.errors())}",
            recovery_instructions=(
                "Please verify that 'ticker' is a non-empty string between 1 and 10 characters "
                "and 'timeframe' is one of ['1D', '1W', '1M', '3M', '1Y', '5Y']."
            ),
            suggested_fix={"ticker": "GOOGL", "timeframe": "1M"}
        ).model_dump()
    except Exception as e:
        return ToolErrorResponse(
            error_code="UNEXPECTED_INPUT_ERROR",
            error_message=str(e),
            recovery_instructions="Pass valid arguments matching the MarketDataRequest Pydantic model.",
            suggested_fix={"ticker": "GOOGL", "timeframe": "1M"}
        ).model_dump()

    # 2. Domain Level Format Validation
    ticker_clean = validated_req.ticker.strip().upper()
    if not re.match(r'^[A-Z0-9.\-]{1,10}$', ticker_clean):
        return ToolErrorResponse(
            error_code="INVALID_TICKER_FORMAT",
            error_message=f"Ticker symbol '{validated_req.ticker}' contains invalid characters.",
            recovery_instructions=(
                "Provide a standard alphanumeric ticker symbol without special characters or spaces (e.g. 'GOOGL', 'NVDA', 'AAPL', 'MSFT')."
            ),
            suggested_fix={"ticker": "GOOGL", "timeframe": validated_req.timeframe}
        ).model_dump()

    valid_timeframes = {"1D", "1W", "1M", "3M", "1Y", "5Y"}
    tf_clean = validated_req.timeframe.strip().upper()
    if tf_clean not in valid_timeframes:
        tf_clean = "1M"

    # 3. Deterministic Mock Market DB
    mock_db = {
        "GOOGL": {
            "company_name": "Alphabet Inc.",
            "price": 182.50,
            "change_30d": +8.4,
            "market_cap": "2.25T",
            "pe_ratio": 24.2,
            "analyst_consensus": "Strong Buy",
            "key_drivers": ["Gemini AI API revenue acceleration", "Cloud profit margin expansion", "Search ad stability"]
        },
        "NVDA": {
            "company_name": "NVIDIA Corporation",
            "price": 128.40,
            "change_30d": +15.2,
            "market_cap": "3.15T",
            "pe_ratio": 48.6,
            "analyst_consensus": "Buy",
            "key_drivers": ["Blackwell architecture demand", "Data center GPU dominance", "Enterprise AI deployment"]
        },
        "MSFT": {
            "company_name": "Microsoft Corporation",
            "price": 448.90,
            "change_30d": +3.1,
            "market_cap": "3.33T",
            "pe_ratio": 35.8,
            "analyst_consensus": "Buy",
            "key_drivers": ["Azure OpenAI enterprise growth", "Copilot 365 adoption", "Gaming revenue integration"]
        },
        "AAPL": {
            "company_name": "Apple Inc.",
            "price": 224.30,
            "change_30d": +6.8,
            "market_cap": "3.44T",
            "pe_ratio": 32.1,
            "analyst_consensus": "Moderate Buy",
            "key_drivers": ["Apple Intelligence rollout", "Services revenue growth", "iPhone upgrade cycle"]
        }
    }

    data = mock_db.get(ticker_clean, {
        "company_name": f"{ticker_clean} Corp",
        "price": 150.00,
        "change_30d": +4.5,
        "market_cap": "500B",
        "pe_ratio": 22.0,
        "analyst_consensus": "Hold",
        "key_drivers": [f"Sector growth in {tf_clean}", "Operational efficiency", "R&D investments"]
    })

    response = MarketDataResponse(
        ticker=ticker_clean,
        company_name=data["company_name"],
        current_price=data["price"],
        currency="USD",
        percent_change_30d=data["change_30d"],
        market_cap=data["market_cap"],
        pe_ratio=data["pe_ratio"],
        analyst_consensus=data["analyst_consensus"],
        key_drivers=data["key_drivers"],
        timeframe=tf_clean
    )
    return response.model_dump()


def search_industry_news(
    request: Optional[NewsSearchRequest] = None,
    *,
    query: Optional[str] = None,
    category: Optional[str] = "general",
    max_results: Optional[int] = 3
) -> Dict[str, Any]:
    """
    Searches for recent market news, regulatory updates, and sector events.

    Args:
        request: Explicit Pydantic NewsSearchRequest schema instance.
        query: Company or industry search query (e.g. 'Cloud AI', 'Alphabet').
        category: News category ('tech', 'finance', 'regulatory', 'general').
        max_results: Maximum articles to return (1-10).

    Returns:
        Validated NewsSearchResponse dictionary or guided ToolErrorResponse with recovery steps.
    """
    # 1. Resolve and Validate Input via Pydantic Schema
    try:
        if request is not None:
            validated_req = request
        else:
            validated_req = NewsSearchRequest(
                query=query or "",
                category=category or "general",
                max_results=max_results if max_results is not None else 3
            )
    except ValidationError as ve:
        return ToolErrorResponse(
            error_code="VALIDATION_ERROR",
            error_message=f"News search input validation failed: {str(ve.errors())}",
            recovery_instructions="Provide a non-empty 'query' string and 'max_results' between 1 and 10.",
            suggested_fix={"query": "AI Agents Market", "category": "tech", "max_results": 3}
        ).model_dump()
    except Exception as e:
        return ToolErrorResponse(
            error_code="UNEXPECTED_INPUT_ERROR",
            error_message=str(e),
            recovery_instructions="Provide valid search parameters matching the NewsSearchRequest Pydantic model.",
            suggested_fix={"query": "Enterprise AI", "category": "tech", "max_results": 3}
        ).model_dump()

    today_str = datetime.date.today().isoformat()
    q = validated_req.query.strip()
    cat = validated_req.category.strip().lower()
    limit = max(1, min(10, validated_req.max_results))

    mock_articles = [
        MarketNewsItem(
            headline=f"Enterprise Adoption of Autonomous Agents Accelerates in {cat.capitalize()}",
            source="Tech Intelligence Daily",
            published_date=today_str,
            summary=f"Key market player '{q}' reported significant ROI gains following deployment of multi-agent AI systems.",
            relevance_score=0.95
        ),
        MarketNewsItem(
            headline=f"Quarterly Sector Outlook: Growth Trends for {q}",
            source="Global Financial Review",
            published_date=today_str,
            summary=f"Analysts highlight strong capital investment and high gross margins across major enterprise solutions related to {q}.",
            relevance_score=0.88
        ),
        MarketNewsItem(
            headline="Regulatory Frameworks and Compliance Benchmarks Updated",
            source="Market Watch Standard",
            published_date=today_str,
            summary="New guidelines emphasize data governance, telemetry transparency, and auditability in automated workflows.",
            relevance_score=0.82
        )
    ]

    response = NewsSearchResponse(
        query=q,
        category=cat,
        total_results=min(limit, len(mock_articles)),
        articles=mock_articles[:limit]
    )
    return response.model_dump()
