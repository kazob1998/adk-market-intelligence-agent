"""
FastAPI Web Server & API Gateway for Google ADK Agent.
Provides interactive web dashboard endpoints, REST API access, live telemetry tracing,
session memory inspection, HITL approval workflows, and benchmark evaluation execution.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from typing import Dict, Any, Optional, List
import os

from src.compat import BaseModel, Field
from src.agent import workflow_executor
from src.memory.memory_manager import memory_manager
from src.observability.telemetry import telemetry
from src.eval.evaluator import evaluator
from src.eval.benchmark_runner import GoldenBenchmarkRunner
from src.orchestration.hitl import hitl_manager
from src.orchestration.model_router import model_router
from src.config import config

app = FastAPI(
    title="ADK Market Intelligence Agent API",
    description="Autonomous Multi-Agent Intelligence System built with Google ADK",
    version="2.0.0"
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


class QueryRequest(BaseModel):
    query: str = Field(description="Market research or company analysis request")
    session_id: Optional[str] = Field(default=None, description="Optional session ID for stateful conversations")
    user_id: Optional[str] = Field(default="default_user", description="User ID identifier")
    require_hitl: Optional[bool] = Field(default=False, description="Require human approval for high-risk proposals")


class EvaluationRequest(BaseModel):
    query: str
    expected_tools: List[str] = Field(default_factory=lambda: ["fetch_market_data", "calculate_risk_and_financial_health", "generate_executive_briefing"])


class HITLDecisionRequest(BaseModel):
    approval_id: str
    decision: str = "APPROVE"  # APPROVE, REJECT, MODIFY
    notes: Optional[str] = None
    modified_payload: Optional[Dict[str, Any]] = None


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the interactive Agent Web Dashboard."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>ADK Market Intelligence Agent API</h1><p>Visit /docs for API schema.</p>")


@app.post("/api/query")
async def execute_agent_query(req: QueryRequest) -> Dict[str, Any]:
    """
    Executes a multi-agent market intelligence workflow request asynchronously.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        result = await workflow_executor.run_intelligence_workflow_async(
            query=req.query,
            session_id=req.session_id,
            user_id=req.user_id or "default_user",
            auto_approve_hitl=not req.require_hitl
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/telemetry")
async def get_telemetry_metrics() -> Dict[str, Any]:
    """
    Returns trace spans, model routing allocations, and latency performance summary.
    """
    return {
        "summary": telemetry.get_metrics_summary(),
        "spans": telemetry.get_trace_spans()
    }


@app.get("/api/memory/{session_id}")
async def get_session_memory(session_id: str) -> Dict[str, Any]:
    """
    Inspects active persistent session state, conversation history, and vector memory index.
    """
    session = await memory_manager.get_or_create_session_async(session_id)
    recalled_memory = await memory_manager.recall_long_term_memory_async("", top_k=10)
    return {
        "session_id": session_id,
        "history": session.history,
        "state_variables": session.state,
        "vector_memory_store": recalled_memory,
        "storage_backend": "SQLite (Persistent)"
    }


@app.post("/api/evaluate")
async def run_automated_evaluation(req: EvaluationRequest) -> Dict[str, Any]:
    """
    Triggers automated benchmark evaluation against the 5 rubric criteria.
    """
    result = await workflow_executor.run_intelligence_workflow_async(query=req.query)
    eval_output = evaluator.evaluate_response(
        query=req.query,
        response_data=result,
        expected_tools=req.expected_tools,
        context_used=True,
        latency_ms=result.get("latency_ms", 150.0)
    )
    return {"status": "success", "evaluation": eval_output.model_dump()}


@app.post("/api/evaluate/golden")
async def run_golden_benchmark() -> Dict[str, Any]:
    """
    Runs the formal Golden Benchmark Regression Suite across all standardized test cases.
    """
    runner = GoldenBenchmarkRunner()
    report = runner.run_benchmark()
    return {
        "status": "success",
        "total_cases": report.total_cases,
        "passed_cases": report.passed_cases,
        "failed_cases": report.failed_cases,
        "pass_rate_pct": report.pass_rate_pct,
        "avg_score": report.avg_score,
        "duration_sec": report.duration_sec,
        "results": report.results
    }


@app.get("/api/hitl/pending")
async def get_pending_approvals() -> Dict[str, Any]:
    """
    Retrieves list of pending Human-in-the-Loop approval requests.
    """
    return {"pending_approvals": hitl_manager.get_pending_requests()}


@app.post("/api/hitl/decision")
async def handle_hitl_decision(req: HITLDecisionRequest) -> Dict[str, Any]:
    """
    Applies human operator decision (APPROVE, REJECT, MODIFY) to a pending approval request.
    """
    decision = req.decision.upper()
    if decision == "APPROVE":
        res = hitl_manager.approve(req.approval_id, req.notes)
    elif decision == "REJECT":
        res = hitl_manager.reject(req.approval_id, req.notes or "Rejected by operator.")
    elif decision == "MODIFY":
        res = hitl_manager.modify(req.approval_id, req.modified_payload or {}, req.notes)
    else:
        raise HTTPException(status_code=400, detail="Decision must be APPROVE, REJECT, or MODIFY.")

    if not res:
        raise HTTPException(status_code=404, detail="Approval ID not found or already resolved.")

    return {"status": "success", "approval": res.model_dump()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
