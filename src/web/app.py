"""
FastAPI Web Server & API Gateway for Google ADK Agent.
Provides interactive web dashboard endpoints, REST API access, live telemetry tracing,
session memory inspection, and benchmark evaluation execution.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import os

from src.agent import workflow_executor
from src.memory.memory_manager import memory_manager
from src.observability.telemetry import telemetry
from src.eval.evaluator import evaluator

app = FastAPI(
    title="ADK Market Intelligence Agent API",
    description="Autonomous Multi-Agent Intelligence System built with Google ADK",
    version="1.0.0"
)

# Static file directory setup
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


class QueryRequest(BaseModel):
    query: str = Field(description="Market research or company analysis request")
    session_id: Optional[str] = Field(default=None, description="Optional session ID for stateful conversations")
    user_id: Optional[str] = Field(default="default_user", description="User ID identifier")


class EvaluationRequest(BaseModel):
    query: str
    expected_tools: List[str] = Field(default_factory=lambda: ["fetch_market_data", "generate_executive_briefing"])


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the interactive Agent Web Dashboard."""
    index_path = os.path.join(static_dir, "index.html")
    return FileResponse(index_path)


@app.post("/api/query")
async def execute_agent_query(req: QueryRequest) -> Dict[str, Any]:
    """
    Executes a multi-agent market intelligence workflow request.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    try:
        result = workflow_executor.run_intelligence_workflow(
            query=req.query,
            session_id=req.session_id,
            user_id=req.user_id
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/telemetry")
async def get_telemetry_metrics() -> Dict[str, Any]:
    """
    Returns trace spans, tool execution metrics, and latency performance summary.
    """
    return {
        "summary": telemetry.get_metrics_summary(),
        "spans": telemetry.get_trace_spans()
    }


@app.get("/api/memory/{session_id}")
async def get_session_memory(session_id: str) -> Dict[str, Any]:
    """
    Inspects active session state, conversation history, and long-term memory store.
    """
    session = memory_manager.get_or_create_session(session_id)
    recalled_memory = memory_manager.recall_long_term_memory("")
    return {
        "session_id": session_id,
        "history": session.history,
        "state_variables": session.state,
        "long_term_memory": recalled_memory
    }


@app.post("/api/evaluate")
async def run_automated_evaluation(req: EvaluationRequest) -> Dict[str, Any]:
    """
    Triggers automated benchmark evaluation against score criteria.
    """
    result = workflow_executor.run_intelligence_workflow(query=req.query)
    eval_output = evaluator.evaluate_response(
        query=req.query,
        response_text=str(result.get("executive_briefing")),
        tools_called=result.get("tools_executed", []),
        expected_tools=req.expected_tools,
        context_used=True,
        latency_ms=result.get("latency_ms", 150.0)
    )
    return {"status": "success", "evaluation": eval_output.model_dump()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
