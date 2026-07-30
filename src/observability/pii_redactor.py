"""
PII Redaction and Data Sanitization Module.
Automatically detects and redacts Personally Identifiable Information (PII)
and sensitive credentials across logs, telemetry traces, session state, and prompts.
"""

import re
from typing import Any, Dict, List, Union


class PIIRedactor:
    """
    High-performance regex-based PII Redactor for enterprise data governance.
    Sanitizes email addresses, phone numbers, SSNs, credit card numbers,
    API keys/tokens, and IP addresses.
    """

    # Compiled patterns for optimal matching speed
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    )
    PHONE_PATTERN = re.compile(
        r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b'
    )
    SSN_PATTERN = re.compile(
        r'\b\d{3}-\d{2}-\d{4}\b'
    )
    CREDIT_CARD_PATTERN = re.compile(
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
    )
    SECRET_KEY_PATTERN = re.compile(
        r'(?:AIza[0-9A-Za-z-_]{35}|Bearer\s+[A-Za-z0-9\-._~+/]+=*|sk-[A-Za-z0-9]{32,}|ghp_[A-Za-z0-9]{36})'
    )
    IP_ADDRESS_PATTERN = re.compile(
        r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    )

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Redacts all PII entities from a text string."""
        if not isinstance(text, str) or not text:
            return text

        scrubbed = cls.EMAIL_PATTERN.sub("[EMAIL_REDACTED]", text)
        scrubbed = cls.SSN_PATTERN.sub("[SSN_REDACTED]", scrubbed)
        scrubbed = cls.CREDIT_CARD_PATTERN.sub("[CARD_REDACTED]", scrubbed)
        scrubbed = cls.SECRET_KEY_PATTERN.sub("[SECRET_REDACTED]", scrubbed)
        scrubbed = cls.PHONE_PATTERN.sub("[PHONE_REDACTED]", scrubbed)
        scrubbed = cls.IP_ADDRESS_PATTERN.sub("[IP_REDACTED]", scrubbed)
        return scrubbed

    @classmethod
    def contains_pii(cls, text: str) -> bool:
        """Returns True if the text contains any detectable PII."""
        if not isinstance(text, str):
            return False
        return bool(
            cls.EMAIL_PATTERN.search(text)
            or cls.SSN_PATTERN.search(text)
            or cls.CREDIT_CARD_PATTERN.search(text)
            or cls.SECRET_KEY_PATTERN.search(text)
        )

    @classmethod
    def redact_object(cls, obj: Any) -> Any:
        """
        Recursively sanitizes dicts, lists, and primitives of any PII.
        """
        if isinstance(obj, str):
            return cls.redact_text(obj)
        elif isinstance(obj, dict):
            return {cls.redact_text(k): cls.redact_object(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [cls.redact_object(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(cls.redact_object(item) for item in obj)
        elif isinstance(obj, set):
            return {cls.redact_object(item) for item in obj}
        return obj


# Global Singleton Instance
pii_redactor = PIIRedactor()
