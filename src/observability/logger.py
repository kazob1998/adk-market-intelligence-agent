"""
Structured Logging & Tracing for Google ADK Agent.
Provides JSON structured logging with trace ID propagation, PII redaction,
and dedicated intent vs. outcome lifecycle tracking.
"""

import logging
import sys
import json
import time
from typing import Dict, Any, Optional

from src.observability.pii_redactor import pii_redactor


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter with automatic PII redaction and distributed trace correlation.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Scrub message of any PII
        clean_message = pii_redactor.redact_text(record.getMessage())

        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": clean_message,
            "trace_id": getattr(record, "trace_id", "none"),
            "span_id": getattr(record, "span_id", "none"),
            "event_type": getattr(record, "event_type", "general"),
        }

        # Include sanitized extra metadata if present
        extra_data = getattr(record, "data", None)
        if extra_data and isinstance(extra_data, dict):
            log_entry["data"] = pii_redactor.redact_object(extra_data)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class AgentLogger(logging.Logger):
    """
    Custom Logger subclass with intent vs outcome tracking methods.
    """

    def log_intent(
        self,
        trace_id: str,
        actor: str,
        intent: str,
        expected_outcome: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Logs the planned intent of a user or agent before execution."""
        extra = {
            "trace_id": trace_id,
            "event_type": "INTENT",
            "data": {
                "actor": actor,
                "intent": intent,
                "expected_outcome": expected_outcome,
                "metadata": metadata or {}
            }
        }
        self.info(f"[INTENT] {actor}: {intent} -> Expecting: {expected_outcome}", extra=extra)

    def log_outcome(
        self,
        trace_id: str,
        actor: str,
        outcome: str,
        success: bool,
        latency_ms: float,
        discrepancy: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Logs the actual outcome and compares against original intent."""
        status_str = "SUCCESS" if success else "FAILURE"
        extra = {
            "trace_id": trace_id,
            "event_type": "OUTCOME",
            "data": {
                "actor": actor,
                "outcome": outcome,
                "status": status_str,
                "latency_ms": latency_ms,
                "discrepancy": discrepancy,
                "metadata": metadata or {}
            }
        }
        self.info(f"[OUTCOME] {actor} ({status_str} in {latency_ms}ms): {outcome}", extra=extra)

    def log_tool_lifecycle(
        self,
        trace_id: str,
        tool_name: str,
        stage: str,  # "BEFORE" or "AFTER"
        payload: Any
    ):
        """Logs tool lifecycle callbacks with sanitized payloads."""
        clean_payload = pii_redactor.redact_object(payload)
        extra = {
            "trace_id": trace_id,
            "event_type": f"TOOL_{stage.upper()}",
            "data": {"tool": tool_name, "stage": stage, "payload": clean_payload}
        }
        self.info(f"[TOOL {stage}] {tool_name}", extra=extra)


logging.setLoggerClass(AgentLogger)


def get_logger(name: str = "adk_agent") -> AgentLogger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger  # type: ignore


logger = get_logger()
