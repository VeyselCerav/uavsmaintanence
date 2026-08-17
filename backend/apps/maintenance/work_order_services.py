from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.core.api_exceptions import (
    InvalidStatusTransition,
    TechnicianInactive,
    WorkOrderAlreadyCompleted,
    WorkOrderAlreadyOpen,
)
from apps.core.models import SystemSetting
from apps.maintenance.enums import (
    OPEN_WORK_ORDER_STATUSES,
    DueStatus,
    MaintenanceType,
    WorkOrderStatus,
)
from apps.maintenance.models import MaintenanceDue, MaintenanceRecord, WorkOrder
from apps.uavs.models import UAV

TRANSITIONS = {
    WorkOrderStatus.OPEN: {WorkOrderStatus.ASSIGNED, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.ASSIGNED: {WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.IN_PROGRESS: {
        WorkOrderStatus.WAITING_PARTS,
        WorkOrderStatus.COMPLETED,
        WorkOrderStatus.CANCELLED,
    },
    WorkOrderStatus.WAITING_PARTS: {
        WorkOrderStatus.IN_PROGRESS,
        WorkOrderStatus.COMPLETED,
        WorkOrderStatus.CANCELLED,
    },
}

AUTO_CREATE_STATUSES = {DueStatus.DUE, DueStatus.OVERDUE, DueStatus.CRITICAL}


class WorkOrderService:
    @staticmethod
    def with_relations(work_order: WorkOrder) -> WorkOrder:
        return WorkOrder.objects.select_related(
            "uav",
            "component",
            "component__component_type",
            "template_item",
            "assigned_technician",
            "assigned_technician__user",
        ).get(pk=work_order.pk)

    @staticmethod
    def next_number() -> str:
        year = timezone.now().year
        prefix = f"WO-{year}-"
        last = (
            WorkOrder.objects.filter(number__startswith=prefix)
            .aggregate(max_number=Max("number"))
            .get("max_number")
        )
        sequence = 1
        if last:
            sequence = int(str(last).rsplit("-", maxsplit=1)[-1]) + 1
        return f"{prefix}{sequence:06d}"

    @staticmethod
    def auto_create_enabled() -> bool:
        setting = SystemSetting.objects.filter(key="work_order.auto_create_on_due").first()
        if setting is None:
            return False
        value = setting.value
        if isinstance(value, bool):
            return value
        if isinstance(value, dict):
            return bool(value.get("enabled"))
        return False

    @classmethod
    def has_open(cls, *, component_id, template_item_id) -> bool:
        return WorkOrder.objects.filter(
            component_id=component_id,
            template_item_id=template_item_id,
            status__in=OPEN_WORK_ORDER_STATUSES,
        ).exists()

    @classmethod
    def create(cls, *, actor, validated_data: dict) -> WorkOrder:
        component = validated_data.get("component")
        template_item = validated_data.get("template_item")
        if component and template_item and cls.has_open(
            component_id=component.id,
            template_item_id=template_item.id,
        ):
            raise WorkOrderAlreadyOpen()
        if template_item:
            validated_data.setdefault("priority", template_item.priority)
            validated_data.setdefault(
                "estimated_duration_minutes",
                template_item.estimated_duration_minutes,
            )
        uav = validated_data["uav"]
        work_order = WorkOrder(**validated_data)
        if not work_order.number:
            work_order.number = cls.next_number()
        work_order.is_demo = bool(getattr(uav, "is_demo", False))
        if work_order.assigned_technician_id:
            work_order.status = WorkOrderStatus.ASSIGNED
        work_order.created_by = actor
        work_order.updated_by = actor
        work_order.save()
        if work_order.assigned_technician_id:
            work_order = cls.with_relations(work_order)
            cls.notify_assigned(work_order)
        return work_order

    @classmethod
    def create_from_due(cls, *, actor, due: MaintenanceDue) -> WorkOrder:
        from apps.fmea.services import MaintenancePriorityService

        return cls.create(
            actor=actor,
            validated_data={
                "uav": due.uav,
                "component": due.component,
                "template_item": due.template_item,
                "maintenance_type": MaintenanceType.PREVENTIVE,
                "priority": MaintenancePriorityService.resolve_for_due(due),
                "notes": "",
            },
        )

    @classmethod
    def sync_auto_create(cls, uav: UAV, dues: list[MaintenanceDue]) -> None:
        if not cls.auto_create_enabled():
            return
        for due in dues:
            if due.status not in AUTO_CREATE_STATUSES:
                continue
            if cls.has_open(component_id=due.component_id, template_item_id=due.template_item_id):
                continue
            cls.create_from_due(actor=None, due=due)

    @classmethod
    def transition(cls, *, actor, work_order: WorkOrder, target: str) -> WorkOrder:
        if work_order.status == WorkOrderStatus.COMPLETED:
            raise WorkOrderAlreadyCompleted()
        allowed = TRANSITIONS.get(work_order.status, set())
        if target not in allowed:
            raise InvalidStatusTransition()
        if target == WorkOrderStatus.COMPLETED:
            return WorkOrderCompletionService.complete(actor=actor, work_order=work_order)
        work_order.status = target
        work_order.updated_by = actor
        now = timezone.now()
        if target == WorkOrderStatus.IN_PROGRESS and work_order.started_at is None:
            work_order.started_at = now
        work_order.save()
        return work_order

    @classmethod
    def assign(cls, *, actor, work_order: WorkOrder, technician) -> WorkOrder:
        from apps.technicians.enums import TechnicianStatus

        if work_order.status not in {WorkOrderStatus.OPEN, WorkOrderStatus.ASSIGNED}:
            raise InvalidStatusTransition()
        user = technician.user
        if technician.status != TechnicianStatus.ACTIVE or not user.is_active:
            raise TechnicianInactive()
        work_order.assigned_technician = technician
        work_order.status = WorkOrderStatus.ASSIGNED
        work_order.updated_by = actor
        work_order.save()
        work_order = cls.with_relations(work_order)
        cls.notify_assigned(work_order)
        return work_order

    @staticmethod
    def notify_assigned(work_order: WorkOrder) -> None:
        from apps.notifications.services import NotificationService

        NotificationService.emit_work_order_assigned(work_order)


class WorkOrderCompletionService:
    @staticmethod
    def complete(*, actor, work_order: WorkOrder) -> WorkOrder:
        if work_order.status == WorkOrderStatus.COMPLETED:
            raise WorkOrderAlreadyCompleted()
        with transaction.atomic():
            locked = (
                WorkOrder.objects.select_for_update(of=("self",))
                .select_related(
                    "uav",
                    "component",
                    "template_item",
                    "assigned_technician",
                    "assigned_technician__user",
                )
                .get(pk=work_order.pk)
            )
            if locked.status == WorkOrderStatus.COMPLETED:
                raise WorkOrderAlreadyCompleted()
            now = timezone.now()
            locked.status = WorkOrderStatus.COMPLETED
            locked.completed_at = now
            locked.updated_by = actor
            locked.save()
            component = locked.component
            hours = Decimal("0")
            cycles = 0
            uav_cycles = locked.uav.total_flight_cycles
            if component is not None:
                hours = Decimal(component.operating_hours)
                cycles = component.cycle_count
                component.last_maintenance_at = now
                component.save(update_fields=["last_maintenance_at", "updated_at"])
            performer = actor
            if locked.assigned_technician_id:
                performer = locked.assigned_technician.user
            MaintenanceRecord.objects.create(
                work_order=locked,
                uav=locked.uav,
                component=component,
                maintenance_type=locked.maintenance_type,
                performed_at=now,
                technician=performer,
                description=locked.template_item.task_name if locked.template_item else "",
                findings=locked.findings,
                approach=locked.uav.maintenance_approach,
                operating_hours_snapshot=hours,
                cycle_count_snapshot=cycles,
                uav_cycles_snapshot=uav_cycles,
                created_by=actor,
                updated_by=actor,
            )
            from apps.maintenance.services import MaintenanceDueService

            MaintenanceDueService.recalculate(locked.uav)
            completed = WorkOrderService.with_relations(locked)
        from apps.notifications.services import NotificationService

        NotificationService.emit_work_order_completed(completed)
        return completed
