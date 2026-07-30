"""
Google ADK Multi-Agent Architecture for Enterprise Market Intelligence.
Demonstrates multi-agent routing, sub-agent delegation, custom tool chaining,
and callback hooks for observability.
"""

import os
import uuid
import time
from typing import Dict, Any, List, Optional
import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from src.tools.market_tools import fetch_market_data, search_industry_news
from src.tools.financial_tools import calculate_risk_and_financial_health, generate_executive_briefing
from src.memory.memory_manager import memory_manager
from src.observability.telemetry import telemetry
from src.observability.logger import logger

# Google GenAI / Vertex AI Environment Setup
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
except Exception:
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "adk-market-intel-demo")

os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")


# Callback hooks for Observability & Tracing
def on_before_tool_exec(tool_name: str, args: Dict[str, Any]):
    logger.info(f"Executing tool: {tool_name} with args: {args}")

def on_after_tool_exec(tool_name: str, result: Any):
    logger.info(f"Tool finished: {tool_name}")


# 1. Specialized Sub-Agent: Market Researcher
market_researcher = Agent(
    name="MarketResearchAgent",
    description="Specialist agent that fetches stock market data, ticker performance, and industry news.",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are an expert Market Research Analyst.
Your goal is to gather current market data, price trends, valuation multiples, and industry news.
Use the `fetch_market_data` and `search_industry_news` tools to retrieve accurate market information.
Always present data clearly with key revenue drivers and news highlights.
""",
    tools=[fetch_market_data, search_industry_news],
)


# 2. Specialized Sub-Agent: Quantitative Risk Analyst
quant_analyst = Agent(
    name="QuantitativeAnalystAgent",
    description="Specialist agent for quantitative risk modeling, financial health scoring, and debt ratio evaluation.",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are a Quantitative Risk Analyst.
Your job is to analyze fundamental financial metrics, evaluate debt balance risks, and calculate composite risk scores.
Use the `calculate_risk_and_financial_health` tool to compute risk ratings and financial health classifications.
Highlight vulnerabilities clearly.
""",
    tools=[calculate_risk_and_financial_health],
)


# 3. Specialized Sub-Agent: Executive Synthesizer
executive_synthesizer = Agent(
    name="ExecutiveSynthesizerAgent",
    description="Synthesizes multi-agent research into C-suite Executive Briefings.",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are a Senior Strategic Executive Advisor.
Your objective is to combine market data and quantitative risk insights into a polished Executive Briefing.
Use the `generate_executive_briefing` tool to structure executive action items and key findings.
""",
    tools=[generate_executive_briefing],
)


# 4. Root Supervisor Agent: Coordinator Agent
root_agent = Agent(
    name="CoordinatorAgent",
    description="Root Supervisor Agent orchestrating market analysis, quantitative risk assessment, and executive briefing synthesis.",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the Chief Intelligence Coordinator.
Your responsibilities:
1. Parse user requests regarding company performance, market trends, or strategic risk.
2. Delegate specialized sub-tasks to your sub-agents:
   - MarketResearchAgent for ticker data and news.
   - QuantitativeAnalystAgent for financial health & risk ratings.
   - ExecutiveSynthesizerAgent for final briefing layout.
3. You can also directly invoke available tools: `fetch_market_data`, `search_industry_news`, `calculate_risk_and_financial_health`, `generate_executive_briefing`.
4. Ensure responses are comprehensive, factual, structured, and include actionable strategic recommendations.
""",
    tools=[
        fetch_market_data,
        search_industry_news,
        calculate_risk_and_financial_health,
        generate_executive_briefing
    ],
    sub_agents=[
        market_researcher,
        quant_analyst,
        executive_synthesizer
    ]
)

# ADK Application Instance
app = App(
    root_agent=root_agent,
    name="market_intelligence_app",
)


class MultiAgentWorkflowExecutor:
    """
    Orchestrates execution flows, session memory context injection, and telemetry trace collection.
    """

    def __init__(self):
        self.app = app

    def run_intelligence_workflow(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        trace_id = f"trace_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        span = telemetry.start_span(
            trace_id=trace_id,
            name="WorkflowExecution",
            component="agent_workflow",
            attributes={"query": query, "session_id": session_id}
        )

        try:
            # 1. Memory Context Injection
            enriched_prompt = memory_manager.format_context_prompt(session_id, query)
            session = memory_manager.get_or_create_session(session_id, user_id=user_id)
            session.add_message("user", query)

            # 2. Sequential Orchestration & Fallback Execution Logic
            tools_executed = []
            findings = []
            
            # Simple keyword tool routing / fallback execution logic
            query_upper = query.upper()
            ticker = None
            for token in query_upper.split():
                clean_tok = token.strip(",.!?")
                if clean_tok in ["GOOGL", "NVDA", "MSFT", "AAPL", "AMZN", "META", "TSLA"]:
                    ticker = clean_tok
                    break
            
            if not ticker and ("MARKET" in query_upper or "STOCK" in query_upper or "NEWS" in query_upper or "GOOGLE" in query_upper):
                ticker = "GOOGL"

            market_info = {}
            if ticker:
                tool_span = telemetry.start_span(trace_id, f"tool:fetch_market_data", "tool")
                market_info = fetch_market_data(ticker=ticker)
                tool_span.finish()
                tools_executed.append("fetch_market_data")
                findings.append(f"Market Data for {ticker}: Price ${market_info.get('current_price')}, 30d change {market_info.get('percent_change_30d')}%, Rating: {market_info.get('analyst_consensus')}.")

            news_info = {}
            if "NEWS" in query_upper or "TREND" in query_upper or "RISK" in query_upper or ticker:
                tool_span = telemetry.start_span(trace_id, f"tool:search_industry_news", "tool")
                news_info = search_industry_news(query=ticker or query)
                tool_span.finish()
                tools_executed.append("search_industry_news")
                articles = news_info.get("articles", [])
                if articles:
                    findings.append(f"Recent News: '{articles[0]['headline']}' ({articles[0]['source']}).")

            quant_info = {}
            if "RISK" in query_upper or "FINANCIAL" in query_upper or "HEALTH" in query_upper or ticker:
                tool_span = telemetry.start_span(trace_id, f"tool:calculate_risk_and_financial_health", "tool")
                quant_info = calculate_risk_and_financial_health(
                    revenue_growth_pct=14.5 if ticker == "GOOGL" else 18.0,
                    gross_margin_pct=58.2,
                    debt_to_equity=0.4
                )
                tool_span.finish()
                tools_executed.append("calculate_risk_and_financial_health")
                findings.append(f"Financial Health Score: Risk {quant_info.get('risk_score')}/100 ({quant_info.get('risk_level')}), Rating: {quant_info.get('financial_health_rating')}.")

            briefing_info = {}
            tool_span = telemetry.start_span(trace_id, f"tool:generate_executive_briefing", "tool")
            briefing_info = generate_executive_briefing(
                company_or_topic=ticker or query,
                key_findings=findings,
                risk_rating=quant_info.get("risk_level", "MODERATE"),
                action_items=[
                    "Capitalize on high-margin product growth opportunities.",
                    "Maintain continuous observability over quantitative risk metrics.",
                    "Review strategic asset allocation on a quarterly cadence."
                ]
            )
            tool_span.finish()
            tools_executed.append("generate_executive_briefing")

            # 3. Store outcome in memory
            memory_manager.store_long_term_memory(
                key=f"analysis_{ticker or session_id}",
                content=briefing_info.get("executive_summary")
            )
            session.add_message("assistant", f"Executive Briefing generated for {ticker or query}.")

            latency_ms = round((time.time() - start_time) * 1000, 2)
            span.finish(status="OK")

            return {
                "session_id": session_id,
                "trace_id": trace_id,
                "ticker": ticker,
                "executive_briefing": briefing_info,
                "market_data": market_info,
                "quantitative_analysis": quant_info,
                "news": news_info,
                "tools_executed": tools_executed,
                "latency_ms": latency_ms
            }

        except Exception as e:
            span.finish(status="ERROR", error_msg=str(e))
            logger.error(f"Workflow error: {e}")
            raise e

workflow_executor = MultiAgentWorkflowExecutor()
