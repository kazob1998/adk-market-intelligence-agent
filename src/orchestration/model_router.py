"""
Strategic Model Routing System for Google ADK Agents.
Implements tiered model routing across Gemini 2.5 Pro, Gemini 2.5 Flash, and Gemini 2.5 Flash-Lite
based on sub-agent domain complexity, reasoning requirements, and SLA latency targets.
"""

from typing import Dict, Any, Optional
from src.compat import BaseModel, Field


class AgentModelPolicy(BaseModel):
    agent_name: str
    model_name: str
    temperature: float
    max_output_tokens: int
    rationale: str


class StrategicModelRouter:
    """
    Manages strategic model allocation across multi-agent hierarchies.
    Routes complex strategic synthesis and coordination to Gemini Pro,
    quantitative risk calculation to Gemini Flash, and high-speed data fetching to Gemini Flash-Lite.
    """

    DEFAULT_ROUTING_MATRIX: Dict[str, AgentModelPolicy] = {
        "CoordinatorAgent": AgentModelPolicy(
            agent_name="CoordinatorAgent",
            model_name="gemini-2.5-pro",
            temperature=0.2,
            max_output_tokens=4096,
            rationale="Requires deep multi-step reasoning, delegation planning, and cross-domain conflict resolution."
        ),
        "ExecutiveSynthesizerAgent": AgentModelPolicy(
            agent_name="ExecutiveSynthesizerAgent",
            model_name="gemini-2.5-pro",
            temperature=0.3,
            max_output_tokens=4096,
            rationale="C-suite strategic synthesis demands high semantic precision and structured decision framing."
        ),
        "QuantitativeAnalystAgent": AgentModelPolicy(
            agent_name="QuantitativeAnalystAgent",
            model_name="gemini-2.5-flash",
            temperature=0.1,
            max_output_tokens=2048,
            rationale="Optimized for rapid mathematical modeling, ratio evaluations, and deterministic scoring."
        ),
        "MarketResearchAgent": AgentModelPolicy(
            agent_name="MarketResearchAgent",
            model_name="gemini-2.5-flash-lite",
            temperature=0.2,
            max_output_tokens=2048,
            rationale="Optimized for low-latency market data extraction and high-throughput news aggregation."
        ),
    }

    def __init__(self, overrides: Optional[Dict[str, str]] = None):
        self.routing_matrix = dict(self.DEFAULT_ROUTING_MATRIX)
        if overrides:
            for agent, model in overrides.items():
                if agent in self.routing_matrix:
                    self.routing_matrix[agent].model_name = model

    def get_model_for_agent(self, agent_name: str) -> str:
        """Returns the assigned Gemini model identifier for a given agent."""
        policy = self.routing_matrix.get(agent_name)
        if policy:
            return policy.model_name
        return "gemini-2.5-flash"

    def get_policy_for_agent(self, agent_name: str) -> AgentModelPolicy:
        """Returns the full AgentModelPolicy configuration."""
        return self.routing_matrix.get(
            agent_name,
            AgentModelPolicy(
                agent_name=agent_name,
                model_name="gemini-2.5-flash",
                temperature=0.2,
                max_output_tokens=2048,
                rationale="Default fallback policy"
            )
        )

    def route_query_dynamically(self, query: str) -> Dict[str, Any]:
        """
        Dynamically analyzes query complexity to recommend optimal agent models.
        """
        query_lower = query.lower()
        complexity_score = 0.0

        # Signals of high complexity (Pro tier)
        if any(term in query_lower for term in ["synthesize", "strategic", "executive briefing", "scenario", "comparative", "cross-sector"]):
            complexity_score += 0.5
        if len(query.split()) > 15:
            complexity_score += 0.3
        if "and" in query_lower and ("risk" in query_lower or "debt" in query_lower):
            complexity_score += 0.2

        tier = "gemini-2.5-pro" if complexity_score >= 0.5 else "gemini-2.5-flash"

        return {
            "query": query,
            "complexity_score": round(complexity_score, 2),
            "recommended_root_model": tier,
            "sub_agent_models": {
                "coordinator": self.get_model_for_agent("CoordinatorAgent"),
                "synthesizer": self.get_model_for_agent("ExecutiveSynthesizerAgent"),
                "quant": self.get_model_for_agent("QuantitativeAnalystAgent"),
                "researcher": self.get_model_for_agent("MarketResearchAgent"),
            }
        }


# Global Singleton Model Router
model_router = StrategicModelRouter()
