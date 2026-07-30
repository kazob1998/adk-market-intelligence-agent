"""
Human-in-the-Loop (HITL) Execution Engine for Google ADK Agent.
Provides approval hooks, interrupt breakpoints, and human review workflows
for high-stakes actions, critical risk ratings, or executive publication.
"""

import uuid
import time
from typing import Dict, List, Any, Optional
from src.compat import BaseModel, Field

from src.observability.logger import logger


class ApprovalRequest(BaseModel):
    approval_id: str = Field(default_factory=lambda: f"hitl_{uuid.uuid4().hex[:8]}")
    action_type: str  # e.g., "PUBLISH_CRITICAL_RISK_BRIEFING", "EXECUTE_STRATEGY"
    title: str
    description: str
    risk_level: str  # LOW, MODERATE, HIGH, CRITICAL
    payload: Dict[str, Any]
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, MODIFIED
    created_at: float = Field(default_factory=time.time)
    reviewed_at: Optional[float] = None
    reviewer_notes: Optional[str] = None


class HITLManager:
    """
    Manages Human-in-the-Loop execution interrupts, pending approvals,
    and decision resolution hooks.
    """

    def __init__(self):
        self._pending_approvals: Dict[str, ApprovalRequest] = {}
        self._history: List[ApprovalRequest] = []

    def should_trigger_approval(self, risk_level: str, action_items: List[str]) -> bool:
        """
        Determines whether an execution plan requires human approval before proceeding.
        Triggers on CRITICAL / HIGH risk classifications or sensitive capital restructuring actions.
        """
        if risk_level.upper() in {"CRITICAL", "HIGH"}:
            return True

        sensitive_keywords = ["restructure", "divest", "refinance", "capital deployment", "layoff"]
        for action in action_items:
            if any(kw in action.lower() for kw in sensitive_keywords):
                return True

        return False

    def create_approval_request(
        self,
        action_type: str,
        title: str,
        description: str,
        risk_level: str,
        payload: Dict[str, Any]
    ) -> ApprovalRequest:
        """Creates and stores a pending approval request."""
        req = ApprovalRequest(
            action_type=action_type,
            title=title,
            description=description,
            risk_level=risk_level,
            payload=payload
        )
        self._pending_approvals[req.approval_id] = req
        logger.info(f"[HITL PENDING] Approval required: {req.approval_id} ({action_type}) - Risk: {risk_level}")
        return req

    def approve(self, approval_id: str, reviewer_notes: Optional[str] = None) -> Optional[ApprovalRequest]:
        """Approves a pending request to resume execution."""
        req = self._pending_approvals.pop(approval_id, None)
        if not req:
            return None

        req.status = "APPROVED"
        req.reviewed_at = time.time()
        req.reviewer_notes = reviewer_notes or "Approved by human operator."
        self._history.append(req)
        logger.info(f"[HITL APPROVED] Approval {approval_id} approved.")
        return req

    def reject(self, approval_id: str, reason: str) -> Optional[ApprovalRequest]:
        """Rejects a pending request."""
        req = self._pending_approvals.pop(approval_id, None)
        if not req:
            return None

        req.status = "REJECTED"
        req.reviewed_at = time.time()
        req.reviewer_notes = reason
        self._history.append(req)
        logger.info(f"[HITL REJECTED] Approval {approval_id} rejected: {reason}")
        return req

    def modify(self, approval_id: str, modified_payload: Dict[str, Any], notes: Optional[str] = None) -> Optional[ApprovalRequest]:
        """Modifies and approves payload with human adjustments."""
        req = self._pending_approvals.pop(approval_id, None)
        if not req:
            return None

        req.status = "MODIFIED"
        req.payload = modified_payload
        req.reviewed_at = time.time()
        req.reviewer_notes = notes or "Modified and approved by human operator."
        self._history.append(req)
        logger.info(f"[HITL MODIFIED] Approval {approval_id} modified.")
        return req

    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Returns all currently pending approval requests."""
        return [req.model_dump() for req in self._pending_approvals.values()]

    def get_request(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Retrieves a specific approval request."""
        return self._pending_approvals.get(approval_id)


# Global Singleton HITL Manager
hitl_manager = HITLManager()
