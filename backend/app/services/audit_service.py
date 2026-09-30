import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def log_audit_event(
    session: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    organization_id: Optional[uuid.UUID] = None,
    actor_user_id: Optional[uuid.UUID] = None,
    previous_state: Optional[Dict[str, Any]] = None,
    new_state: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Create and persist an audit log event in PostgreSQL."""
    audit_entry = AuditLog(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_state=previous_state,
        new_state=new_state,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(audit_entry)
    await session.flush()
    return audit_entry
