"""
Observability & Tracing System for Google ADK Agent.
Collects trace spans, tool execution latencies, token consumption estimates,
and event logs for evaluation and monitoring dashboard.
"""

import time
import uuid
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from src.observability.logger import logger


class TraceSpan(BaseModel):
    span_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    trace_id: str
    name: str
    component: str  # agent, tool, memory, flow
    status: str = "OK"  # OK, ERROR
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    events: List[Dict[str, Any]] = Field(default_factory=list)

    def finish(self, status: str = "OK", error_msg: Optional[str] = None):
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        self.status = status
        if error_msg:
            self.attributes["error"] = error_msg


class TelemetryCollector:
    """
    Central telemetry collector for ADK execution tracing.
    Stores spans and metrics in memory and exposes JSON export for monitoring dashboard.
    """

    def __init__(self):
        self._spans: List[TraceSpan] = []
        self._active_spans: Dict[str, TraceSpan] = {}

    def start_span(self, trace_id: str, name: str, component: str, attributes: Optional[Dict[str, Any]] = None) -> TraceSpan:
        span = TraceSpan(
            trace_id=trace_id,
            name=name,
            component=component,
            attributes=attributes or {}
        )
        self._active_spans[span.span_id] = span
        logger.info(f"[SPAN START] {name} (trace_id={trace_id})", extra={"trace_id": trace_id, "span_id": span.span_id})
        return span

    def end_span(self, span: TraceSpan, status: str = "OK", error_msg: Optional[str] = None):
        span.finish(status=status, error_msg=error_msg)
        if span.span_id in self._active_spans:
            del self._active_spans[span.span_id]
        self._spans.append(span)
        logger.info(f"[SPAN END] {span.name} - {span.duration_ms}ms [{status}]", extra={"trace_id": span.trace_id, "span_id": span.span_id})

    def get_trace_spans(self, trace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if trace_id:
            spans = [s for s in self._spans if s.trace_id == trace_id]
        else:
            spans = self._spans
        return [s.model_dump() for s in spans]

    def get_metrics_summary(self) -> Dict[str, Any]:
        total_spans = len(self._spans)
        if total_spans == 0:
            return {"total_spans": 0, "avg_duration_ms": 0, "success_rate": 1.0}

        successful = [s for s in self._spans if s.status == "OK"]
        total_dur = sum(s.duration_ms for s in self._spans if s.duration_ms)
        
        return {
            "total_spans": total_spans,
            "successful_spans": len(successful),
            "failed_spans": total_spans - len(successful),
            "success_rate": round(len(successful) / total_spans, 4),
            "avg_duration_ms": round(total_dur / total_spans, 2),
            "total_tool_calls": len([s for s in self._spans if s.component == "tool"])
        }

telemetry = TelemetryCollector()
