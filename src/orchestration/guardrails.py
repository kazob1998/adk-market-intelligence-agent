"""
Active Runtime Guardrails & ADK Policy Plugin for Google ADK Agent.
Provides pre-execution prompt safety checks, jailbreak prevention, tool policy enforcement,
and post-execution regulatory compliance validation.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from src.compat import BaseModel, Field

from src.observability.pii_redactor import pii_redactor
from src.observability.logger import logger


class GuardrailCheckResult(BaseModel):
    passed: bool
    guardrail_type: str  # PRE_EXECUTION, TOOL_POLICY, POST_EXECUTION
    violation_code: Optional[str] = None
    violation_message: Optional[str] = None
    sanitized_output: Optional[Any] = None


class ActiveRuntimeGuardrails:
    """
    Active policy plugin executing guardrail checks across every stage of the ADK workflow.
    """

    # Known prompt injection / jailbreak patterns
    INJECTION_PATTERNS = [
        re.compile(r'ignore\s+(all\s+)?(previous|prior)\s+instructions', re.IGNORECASE),
        re.compile(r'reveal\s+(your\s+)?system\s+prompt', re.IGNORECASE),
        re.compile(r'bypass\s+all\s+(safety|rules|constraints)', re.IGNORECASE),
        re.compile(r'act\s+as\s+an\s+unregulated\s+financial\s+advisor', re.IGNORECASE),
        re.compile(r'guarantee\s+100%\s+stock\s+returns', re.IGNORECASE),
    ]

    MANDATORY_DISCLAIMER = (
        "Generated autonomously by ADK Market Intelligence Agent System. "
        "For analytical research and strategic planning only; not registered investment advice."
    )

    def evaluate_input_guardrail(self, query: str) -> GuardrailCheckResult:
        """
        Pre-Execution Guardrail: Checks prompt for injection, safety violations, and sanitizes PII.
        """
        # 1. Jailbreak / Prompt Injection Check
        for pattern in self.INJECTION_PATTERNS:
            if pattern.search(query):
                logger.warning(f"[GUARDRAIL VIOLATION] Prompt injection detected: '{query}'")
                return GuardrailCheckResult(
                    passed=False,
                    guardrail_type="PRE_EXECUTION",
                    violation_code="PROMPT_INJECTION_DETECTED",
                    violation_message="Query contains adversarial instructions or attempts to bypass safety constraints."
                )

        # 2. PII Sanitization
        sanitized_query = pii_redactor.redact_text(query)

        return GuardrailCheckResult(
            passed=True,
            guardrail_type="PRE_EXECUTION",
            sanitized_output=sanitized_query
        )

    def evaluate_tool_policy(self, tool_name: str, args: Dict[str, Any]) -> GuardrailCheckResult:
        """
        Tool Policy Guardrail: Validates argument bounds and enforces calling rules.
        """
        if tool_name == "calculate_risk_and_financial_health":
            debt = args.get("debt_to_equity")
            margin = args.get("gross_margin_pct")
            if debt is not None and debt < 0:
                return GuardrailCheckResult(
                    passed=False,
                    guardrail_type="TOOL_POLICY",
                    violation_code="INVALID_FINANCIAL_RATIO",
                    violation_message="Debt-to-equity ratio cannot be negative."
                )
            if margin is not None and (margin < 0 or margin > 100):
                return GuardrailCheckResult(
                    passed=False,
                    guardrail_type="TOOL_POLICY",
                    violation_code="INVALID_MARGIN_RATIO",
                    violation_message="Gross margin percentage must be between 0 and 100."
                )

        return GuardrailCheckResult(
            passed=True,
            guardrail_type="TOOL_POLICY",
            sanitized_output=args
        )

    def evaluate_output_guardrail(self, briefing_dict: Dict[str, Any]) -> Tuple[Dict[str, Any], GuardrailCheckResult]:
        """
        Post-Execution Guardrail: Enforces mandatory regulatory disclaimer,
        checks sanity of risk ratings, and redacts any residual PII.
        """
        validated_briefing = pii_redactor.redact_object(dict(briefing_dict))

        # Enforce regulatory disclaimer
        if not validated_briefing.get("disclaimer"):
            validated_briefing["disclaimer"] = self.MANDATORY_DISCLAIMER
        elif "analytical" not in validated_briefing.get("disclaimer", "").lower():
            validated_briefing["disclaimer"] = self.MANDATORY_DISCLAIMER

        # Sanity check: Ensure rating is valid
        rating = validated_briefing.get("composite_risk_rating", "MODERATE").upper()
        if rating not in {"LOW", "MODERATE", "HIGH", "CRITICAL"}:
            validated_briefing["composite_risk_rating"] = "MODERATE"

        return validated_briefing, GuardrailCheckResult(
            passed=True,
            guardrail_type="POST_EXECUTION",
            sanitized_output=validated_briefing
        )


# Global Singleton Guardrails
guardrails = ActiveRuntimeGuardrails()
