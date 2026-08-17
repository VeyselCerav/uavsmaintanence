from __future__ import annotations

from uuid import UUID

from apps.audit.enums import AuditAction
from apps.audit.models import AuditLog


def client_ip(request) -> str:
    if request is None:
        return ""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.META.get("REMOTE_ADDR") or "")[:64]


class AuditService:
    @staticmethod
    def log(
        *,
        actor=None,
        action: str,
        entity_type: str,
        entity_id: UUID | str | None = None,
        old_value=None,
        new_value=None,
        message: str = "",
        ip: str = "",
        request=None,
    ) -> AuditLog:
        if action not in AuditAction.values:
            action = AuditAction.UPDATE
        return AuditLog.objects.create(
            user=actor,
            ip=ip or client_ip(request),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            message=message,
        )
