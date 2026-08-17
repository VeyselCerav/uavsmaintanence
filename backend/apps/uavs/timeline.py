from __future__ import annotations

from apps.components.models import UAVComponent
from apps.documents.models import Document
from apps.failures.models import Failure
from apps.flights.models import Flight
from apps.maintenance.models import MaintenanceRecord, WorkOrder
from apps.uavs.models import UAV

LIMIT = 100


def _event(*, occurred_at, event_type: str, detail: str, entity_id) -> dict:
    return {
        "occurred_at": occurred_at.isoformat() if occurred_at else None,
        "event_type": event_type,
        "detail": detail,
        "entity_id": str(entity_id) if entity_id else None,
    }


class TimelineService:
    @classmethod
    def for_uav(cls, uav: UAV) -> list[dict]:
        events: list[dict] = [
            _event(
                occurred_at=uav.created_at,
                event_type="UAV_CREATED",
                detail=uav.registration_number,
                entity_id=uav.id,
            )
        ]
        for component in UAVComponent.objects.filter(uav=uav):
            if component.installed_at:
                events.append(
                    _event(
                        occurred_at=component.installed_at,
                        event_type="COMPONENT_INSTALLED",
                        detail=component.name,
                        entity_id=component.id,
                    )
                )
            if component.removed_at:
                events.append(
                    _event(
                        occurred_at=component.removed_at,
                        event_type="COMPONENT_REMOVED",
                        detail=component.name,
                        entity_id=component.id,
                    )
                )
        for flight in Flight.objects.filter(uav=uav):
            events.append(
                _event(
                    occurred_at=flight.start_at,
                    event_type="FLIGHT",
                    detail=flight.flight_number,
                    entity_id=flight.id,
                )
            )
        for work_order in WorkOrder.objects.filter(uav=uav):
            events.append(
                _event(
                    occurred_at=work_order.created_at,
                    event_type="WORK_ORDER",
                    detail=work_order.number,
                    entity_id=work_order.id,
                )
            )
        for record in MaintenanceRecord.objects.filter(uav=uav):
            events.append(
                _event(
                    occurred_at=record.performed_at,
                    event_type="MAINTENANCE",
                    detail=record.maintenance_type,
                    entity_id=record.id,
                )
            )
        for failure in Failure.objects.filter(uav=uav).select_related("failure_mode"):
            if failure.failure_mode_id:
                detail = failure.failure_mode.code
            else:
                detail = (failure.description or "")[:80]
            events.append(
                _event(
                    occurred_at=failure.occurred_at,
                    event_type="FAILURE",
                    detail=detail,
                    entity_id=failure.id,
                )
            )
        for document in Document.objects.filter(uav=uav):
            events.append(
                _event(
                    occurred_at=document.created_at,
                    event_type="DOCUMENT",
                    detail=document.title,
                    entity_id=document.id,
                )
            )
        events = [item for item in events if item["occurred_at"]]
        events.sort(key=lambda item: item["occurred_at"], reverse=True)
        return events[:LIMIT]
