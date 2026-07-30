"""
Automated Evaluation Suite for Google ADK Agent.
Measures agent performance against 5 core benchmark metrics:
1. Tool Usage Accuracy
2. Response Relevance
3. Context Retention & Memory Integration
4. Execution Latency
5. Structured Output Formatting
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
import time


class EvaluationResult(BaseModel):
    test_case: str
    overall_score: float = Field(description="Score out of 100")
    tool_usage_score: float
    relevance_score: float
    memory_context_score: float
    latency_score: float
    output_format_score: float
    feedback: List[str]
    latency_ms: float


class AgentEvaluator:
    """
    Automated evaluator for ADK Market Intelligence Agent runs.
    """

    def evaluate_response(
        self,
        query: str,
        response_text: str,
        tools_called: List[str],
        expected_tools: List[str],
        context_used: bool,
        latency_ms: float
    ) -> EvaluationResult:
        feedback = []

        # 1. Tool Usage Score (25 pts)
        if expected_tools:
            matched_tools = [t for t in expected_tools if t in tools_called]
            tool_score = (len(matched_tools) / len(expected_tools)) * 25.0
            if tool_score < 25.0:
                feedback.append(f"Missing expected tools: {set(expected_tools) - set(tools_called)}")
        else:
            tool_score = 25.0

        # 2. Relevance Score (25 pts)
        relevance_score = 25.0
        query_terms = [word.lower() for word in query.split() if len(word) > 3]
        matched_terms = [t for t in query_terms if t in response_text.lower()]
        if query_terms and len(matched_terms) == 0:
            relevance_score = 10.0
            feedback.append("Response content does not directly address key query terms.")

        # 3. Context & Memory Score (20 pts)
        memory_score = 20.0 if context_used else 15.0
        if not context_used:
            feedback.append("Session state context was not explicitly referenced in prompt.")

        # 4. Latency Score (15 pts)
        if latency_ms < 1000:
            latency_score = 15.0
        elif latency_ms < 3000:
            latency_score = 12.0
        else:
            latency_score = 8.0
            feedback.append(f"Execution latency ({round(latency_ms, 1)}ms) exceeded benchmark 1000ms target.")

        # 5. Output Format Score (15 pts)
        output_format_score = 15.0
        if "Briefing" in response_text or "Executive" in response_text or "Risk Score" in response_text or "Market" in response_text:
            output_format_score = 15.0
        else:
            output_format_score = 10.0

        overall = round(tool_score + relevance_score + memory_score + latency_score + output_format_score, 1)

        return EvaluationResult(
            test_case=query,
            overall_score=overall,
            tool_usage_score=round(tool_score, 1),
            relevance_score=round(relevance_score, 1),
            memory_context_score=round(memory_score, 1),
            latency_score=round(latency_score, 1),
            output_format_score=round(output_format_score, 1),
            feedback=feedback,
            latency_ms=round(latency_ms, 2)
        )

evaluator = AgentEvaluator()
