"""
Observability & Tracing System for Google ADK Agent.
Collects trace spans, tool execution latencies, token consumption estimates,
intent vs. outcome verification, and event logs for evaluation and monitoring dashboard.
"""

import time
import uuid
from typing import Dict, List, Any, Optional
from src.compat import BaseModel, Field

from src.observability.logger import logger
from src.observability.pii_redactor import pii_redactor


class IntentOutcomeRecord(BaseModel):
    intent_statement: str
    target_tools: List[str] = Field(default_factory=list)
    actual_tools_executed: List[str] = Field(default_factory=list)
    outcome_summary: Optional[str] = None
    alignment_score: float = 1.0  # 0.0 to 1.0
    discrepancy: Optional[str] = None


class TraceSpan(BaseModel):
    span_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    trace_id: str
    name: str
    component: str  # agent, tool, memory, guardrail, hitl, flow
    status: str = "OK"  # OK, ERROR, PENDING_APPROVAL
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    model_tier: Optional[str] = None  # e.g., gemini-2.5-pro, gemini-2.5-flash
    attributes: Dict[str, Any] = Field(default_factory=dict)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    intent_outcome: Optional[IntentOutcomeRecord] = None

    def add_event(self, name: str, data: Optional[Dict[str, Any]] = None):
        sanitized_data = pii_redactor.redact_object(data or {})
        self.events.append({
            "timestamp": time.time(),
            "name": name,
            "data": sanitized_data
        })

    def record_intent(self, intent: str, target_tools: Optional[List[str]] = None):
        self.intent_outcome = IntentOutcomeRecord(
            intent_statement=pii_redactor.redact_text(intent),
            target_tools=target_tools or []
        )
        self.add_event("intent_registered", {"intent": self.intent_outcome.intent_statement})

    def record_outcome(
        self,
        outcome_summary: str,
        tools_executed: Optional[List[str]] = None,
        alignment_score: float = 1.0,
        discrepancy: Optional[str] = None
    ):
        if not self.intent_outcome:
            self.intent_outcome = IntentOutcomeRecord(intent_statement="Unspecified")
        self.intent_outcome.outcome_summary = pii_redactor.redact_text(outcome_summary)
        self.intent_outcome.actual_tools_executed = tools_executed or []
        self.intent_outcome.alignment_score = alignment_score
        self.intent_outcome.discrepancy = discrepancy
        self.add_event("outcome_registered", {
            "summary": self.intent_outcome.outcome_summary,
            "alignment": alignment_score,
            "discrepancy": discrepancy
        })

    def finish(self, status: str = "OK", error_msg: Optional[str] = None):
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        self.status = status
        if error_msg:
            self.attributes["error"] = pii_redactor.redact_text(error_msg)


class TelemetryCollector:
    """
    Central telemetry collector for ADK execution tracing.
    Stores spans and metrics with automatic PII redaction and exposes JSON export.
    """

    def __init__(self):
        self._spans: List[TraceSpan] = []
        self._active_spans: Dict[str, TraceSpan] = {}

    def start_span(
        self,
        trace_id: str,
        name: str,
        component: str,
        attributes: Optional[Dict[str, Any]] = None,
        model_tier: Optional[str] = None
    ) -> TraceSpan:
        sanitized_attrs = pii_redactor.redact_object(attributes or {})
        span = TraceSpan(
            trace_id=trace_id,
            name=name,
            component=component,
            model_tier=model_tier,
            attributes=sanitized_attrs
        )
        self._active_spans[span.span_id] = span
        logger.info(
            f"[SPAN START] {name} (trace_id={trace_id})",
            extra={"trace_id": trace_id, "span_id": span.span_id, "data": sanitized_attrs}
        )
        return span

    def end_span(self, span: TraceSpan, status: str = "OK", error_msg: Optional[str] = None):
        span.finish(status=status, error_msg=error_msg)
        if span.span_id in self._active_spans:
            del self._active_spans[span.span_id]
        self._spans.append(span)
        logger.info(
            f"[SPAN END] {span.name} - {span.duration_ms}ms [{status}]",
            extra={"trace_id": span.trace_id, "span_id": span.span_id}
        )

    def get_trace_spans(self, trace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if trace_id:
            spans = [s for s in self._spans if s.trace_id == trace_id]
        else:
            spans = self._spans
        return [s.model_dump() for s in spans]

    def get_metrics_summary(self) -> Dict[str, Any]:
        total_spans = len(self._spans)
        if total_spans == 0:
            return {
                "total_spans": 0,
                "avg_duration_ms": 0,
                "success_rate": 1.0,
                "model_routing_counts": {},
                "total_tool_calls": 0
            }

        successful = [s for s in self._spans if s.status == "OK"]
        total_dur = sum(s.duration_ms for s in self._spans if s.duration_ms)

        # Count model tier allocations
        model_counts = {}
        for s in self._spans:
            if s.model_tier:
                model_counts[s.model_tier] = model_counts.get(s.model_tier, 0) + 1

        return {
            "total_spans": total_spans,
            "successful_spans": len(successful),
            "failed_spans": total_spans - len(successful),
            "success_rate": round(len(successful) / total_spans, 4),
            "avg_duration_ms": round(total_dur / total_spans, 2),
            "total_tool_calls": len([s for s in self._spans if s.component == "tool"]),
            "model_routing_counts": model_counts
        }

    def clear(self):
        """Clears stored spans (useful for tests)."""
        self._spans.clear()
        self._active_spans.clear()


telemetry = TelemetryCollector()
