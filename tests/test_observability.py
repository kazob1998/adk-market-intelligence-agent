"""
Unit tests for Observability, Structured Logging, Intent vs Outcome Tracing, and PII Redaction.
"""

import unittest
import json
import logging
from src.observability.pii_redactor import pii_redactor
from src.observability.logger import logger, JSONFormatter
from src.observability.telemetry import telemetry


class TestObservability(unittest.TestCase):

    def test_pii_redaction_rules(self):
        text = "Contact ceo@enterprise.com or call 555-123-4567. SSN is 000-12-3456 and token is sk-12345678901234567890123456789012"
        scrubbed = pii_redactor.redact_text(text)

        self.assertNotIn("ceo@enterprise.com", scrubbed)
        self.assertIn("[EMAIL_REDACTED]", scrubbed)
        self.assertNotIn("555-123-4567", scrubbed)
        self.assertIn("[PHONE_REDACTED]", scrubbed)
        self.assertNotIn("000-12-3456", scrubbed)
        self.assertIn("[SSN_REDACTED]", scrubbed)
        self.assertIn("[SECRET_REDACTED]", scrubbed)

    def test_json_formatter_with_pii_scrubbing(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="User alert for analyst@fund.com",
            args=(),
            exc_info=None
        )
        record.trace_id = "trace_abc123"
        record.span_id = "span_xyz789"

        formatted = formatter.format(record)
        data = json.loads(formatted)

        self.assertEqual(data["trace_id"], "trace_abc123")
        self.assertEqual(data["span_id"], "span_xyz789")
        self.assertNotIn("analyst@fund.com", data["message"])
        self.assertIn("[EMAIL_REDACTED]", data["message"])

    def test_telemetry_span_lifecycle_and_intent_outcome(self):
        span = telemetry.start_span(
            trace_id="test_tr_001",
            name="test_operation",
            component="agent",
            model_tier="gemini-2.5-pro"
        )
        span.record_intent(intent="Extract financial health and risk score", target_tools=["fetch_market_data"])
        span.record_outcome(outcome_summary="Financial health AA extracted", tools_executed=["fetch_market_data"])
        telemetry.end_span(span, status="OK")

        spans = telemetry.get_trace_spans("test_tr_001")
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0]["model_tier"], "gemini-2.5-pro")
        self.assertIsNotNone(spans[0]["intent_outcome"])
        self.assertEqual(spans[0]["intent_outcome"]["alignment_score"], 1.0)


if __name__ == "__main__":
    unittest.main()
