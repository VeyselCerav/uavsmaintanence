from __future__ import annotations

from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.audit.enums import AuditAction
from apps.audit.services import AuditService
from apps.components.enums import ComponentStatus
from apps.components.models import UAVComponent
from apps.core.api_exceptions import (
    ComponentHasOpenWorkOrder,
    ComponentNotInstalled,
    ComponentSerialTaken,
    ComponentTypeInactive,
    ComponentUavRetired,
    InvalidComponentDates,
)
from apps.maintenance.enums import OPEN_WORK_ORDER_STATUSES
from apps.maintenance.models import WorkOrder
from apps.uavs.enums import UAVStatus


class ComponentService:
    @staticmethod
    def with_relations(component: UAVComponent) -> UAVComponent:
        return UAVComponent.objects.select_related("uav", "component_type").get(pk=component.pk)

    @staticmethod
    def _serial_taken(*, serial: str, exclude_id=None) -> bool:
        if not serial:
            return False
        queryset = UAVComponent.objects.filter(
            serial_number=serial,
            status=ComponentStatus.INSTALLED,
            removed_at__isnull=True,
        )
        if exclude_id:
            queryset = queryset.exclude(pk=exclude_id)
        return queryset.exists()

    @classmethod
    def install(cls, *, actor, data: dict, request=None) -> UAVComponent:
        uav = data["uav"]
        component_type = data["component_type"]
        if uav.status == UAVStatus.RETIRED:
            raise ComponentUavRetired()
        if not component_type.is_active:
            raise ComponentTypeInactive()
        serial = (data.get("serial_number") or "").strip()
        if cls._serial_taken(serial=serial):
            raise ComponentSerialTaken()
        name = (data.get("name") or "").strip() or component_type.name
        installed_at = data.get("installed_at") or timezone.now()
        component = UAVComponent(
            uav=uav,
            component_type=component_type,
            name=name,
            serial_number=serial,
            part_number=(data.get("part_number") or "").strip(),
            manufacturer=(data.get("manufacturer") or "").strip(),
            model=(data.get("model") or "").strip(),
            installed_at=installed_at,
            removed_at=None,
            operating_hours=Decimal(str(data.get("operating_hours") or 0)),
            cycle_count=int(data.get("cycle_count") or 0),
            status=ComponentStatus.INSTALLED,
            notes=(data.get("notes") or "").strip(),
            is_demo=uav.is_demo,
            created_by=actor,
            updated_by=actor,
        )
        try:
            with transaction.atomic():
                component.save()
                from apps.maintenance.services import MaintenanceDueService

                MaintenanceDueService.recalculate(uav)
        except IntegrityError as exc:
            raise ComponentSerialTaken() from exc
        AuditService.log(
            actor=actor,
            action=AuditAction.CREATE,
            entity_type="UAVComponent",
            entity_id=component.id,
            new_value={
                "uav": str(uav.id),
                "serial_number": component.serial_number,
                "status": component.status,
            },
            message="component.install",
            request=request,
        )
        return cls.with_relations(component)

    @classmethod
    def update(cls, *, actor, component: UAVComponent, data: dict, request=None) -> UAVComponent:
        old = {"name": component.name, "notes": component.notes}
        for field in ("name", "part_number", "manufacturer", "model", "notes"):
            if field in data and data[field] is not None:
                value = data[field]
                setattr(component, field, value.strip() if isinstance(value, str) else value)
        component.updated_by = actor
        component.save()
        AuditService.log(
            actor=actor,
            action=AuditAction.UPDATE,
            entity_type="UAVComponent",
            entity_id=component.id,
            old_value=old,
            new_value={"name": component.name, "notes": component.notes},
            message="component.update",
            request=request,
        )
        return cls.with_relations(component)

    @classmethod
    def remove(cls, *, actor, component: UAVComponent, data: dict, request=None) -> UAVComponent:
        if component.status != ComponentStatus.INSTALLED or component.removed_at is not None:
            raise ComponentNotInstalled()
        if component.uav.status == UAVStatus.RETIRED:
            raise ComponentUavRetired()
        if WorkOrder.objects.filter(
            component=component,
            status__in=OPEN_WORK_ORDER_STATUSES,
        ).exists():
            raise ComponentHasOpenWorkOrder()
        removed_at = data.get("removed_at") or timezone.now()
        if component.installed_at and removed_at < component.installed_at:
            raise InvalidComponentDates()
        old_status = component.status
        component.status = data.get("status") or ComponentStatus.REMOVED
        component.removed_at = removed_at
        extra_notes = (data.get("notes") or "").strip()
        if extra_notes:
            component.notes = f"{component.notes}\n{extra_notes}".strip() if component.notes else extra_notes
        component.updated_by = actor
        with transaction.atomic():
            component.save()
            from apps.maintenance.services import MaintenanceDueService

            MaintenanceDueService.recalculate(component.uav)
        AuditService.log(
            actor=actor,
            action=AuditAction.UPDATE,
            entity_type="UAVComponent",
            entity_id=component.id,
            old_value={"status": old_status, "removed_at": None},
            new_value={"status": component.status, "removed_at": str(component.removed_at)},
            message="component.remove",
            request=request,
        )
        return cls.with_relations(component)
