from datetime import datetime, timezone
from typing import Any, Dict, Optional
from app.core.logging import logger, correlation_id_ctx


class AuditEvent:
    def __init__(
        self,
        action: str,
        actor_id: Optional[int] = None,
        actor_role: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
    ):
        self.action = action
        self.actor_id = actor_id
        self.actor_role = actor_role
        self.target_type = target_type
        self.target_id = target_id
        self.details = details or {}
        self.status = status
        self.correlation_id = correlation_id_ctx.get() or "unknown"
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "details": self.details,
            "status": self.status,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
        }


def emit_audit_event(
    action: str,
    actor_id: Optional[int] = None,
    actor_role: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    status: str = "SUCCESS",
) -> AuditEvent:
    """Log an audit event and return the event object."""
    event = AuditEvent(
        action=action,
        actor_id=actor_id,
        actor_role=actor_role,
        target_type=target_type,
        target_id=target_id,
        details=details,
        status=status,
    )
    logger.info(f"AUDIT_EVENT: {event.action}", extra={"audit": event.to_dict()})
    return event
