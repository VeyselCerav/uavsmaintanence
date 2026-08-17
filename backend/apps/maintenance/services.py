from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db.models import Max
from django.utils import timezone

from apps.components.enums import ComponentStatus
from apps.components.models import UAVComponent
from apps.core.api_exceptions import InvalidDueRules, TemplateNotFound
from apps.core.models import SystemSetting
from apps.maintenance.enums import DueStatus, IntervalUnit
from apps.maintenance.models import (
    MaintenanceDue,
    MaintenanceRecord,
    MaintenanceTemplate,
    MaintenanceTemplateItem,
)
from apps.uavs.models import UAV

DEFAULT_DUE_RULES = {
    "approaching_percent": 80,
    "due_percent": 100,
    "overdue_percent": 110,
    "critical_percent": 130,
}

DAYS_PER_MONTH = Decimal("30.4375")
DAYS_PER_YEAR = Decimal("365.25")


class TemplateResolveService:
    @staticmethod
    def resolve(uav_class_id, platform_type_id, mission_type_id, approach: str):
        template = MaintenanceTemplate.objects.filter(
            uav_class_id=uav_class_id,
            platform_type_id=platform_type_id,
            mission_type_id=mission_type_id,
            approach=approach,
            is_active=True,
        ).first()
        if template is None:
            raise TemplateNotFound()
        return template


class DueRulesService:
    KEY_RULES = "maintenance.due_rules"
    KEY_AUTO_CREATE = "work_order.auto_create_on_due"

    @classmethod
    def get(cls) -> dict[str, Decimal]:
        setting = SystemSetting.objects.filter(key=cls.KEY_RULES).first()
        raw = setting.value if setting else DEFAULT_DUE_RULES
        if not isinstance(raw, dict):
            raw = DEFAULT_DUE_RULES
        return {
            "approaching_percent": Decimal(str(raw.get("approaching_percent", 80))),
            "due_percent": Decimal(str(raw.get("due_percent", 100))),
            "overdue_percent": Decimal(str(raw.get("overdue_percent", 110))),
            "critical_percent": Decimal(str(raw.get("critical_percent", 130))),
        }

    @classmethod
    def auto_create_enabled(cls) -> bool:
        from apps.maintenance.work_order_services import WorkOrderService

        return WorkOrderService.auto_create_enabled()

    @classmethod
    def get_payload(cls) -> dict:
        rules = cls.get()
        return {
            "approaching_percent": float(rules["approaching_percent"]),
            "due_percent": float(rules["due_percent"]),
            "overdue_percent": float(rules["overdue_percent"]),
            "critical_percent": float(rules["critical_percent"]),
            "auto_create_on_due": cls.auto_create_enabled(),
        }

    @classmethod
    def update(cls, *, actor, validated_data: dict) -> dict:
        approaching = Decimal(str(validated_data["approaching_percent"]))
        due = Decimal(str(validated_data["due_percent"]))
        overdue = Decimal(str(validated_data["overdue_percent"]))
        critical = Decimal(str(validated_data["critical_percent"]))
        if not (Decimal("0") < approaching < due < overdue < critical):
            raise InvalidDueRules()
        rules = {
            "approaching_percent": float(approaching),
            "due_percent": float(due),
            "overdue_percent": float(overdue),
            "critical_percent": float(critical),
        }
        SystemSetting.objects.update_or_create(
            key=cls.KEY_RULES,
            defaults={
                "value": rules,
                "description": "Due status percent thresholds",
                "updated_by": actor,
            },
        )
        SystemSetting.objects.update_or_create(
            key=cls.KEY_AUTO_CREATE,
            defaults={
                "value": bool(validated_data["auto_create_on_due"]),
                "description": "Create OPEN work order when due threshold is crossed",
                "updated_by": actor,
            },
        )
        for uav in UAV.objects.all():
            MaintenanceDueService.recalculate(uav)
        return cls.get_payload()


class TemplateItemService:
    @staticmethod
    def next_sequence(template: MaintenanceTemplate) -> int:
        current = MaintenanceTemplateItem.objects.filter(template=template).aggregate(
            max_seq=Max("sequence")
        )["max_seq"]
        return int(current or 0) + 1

    @classmethod
    def create(cls, *, actor, template: MaintenanceTemplate, validated_data: dict):
        item = MaintenanceTemplateItem(template=template, **validated_data)
        if not item.sequence:
            item.sequence = cls.next_sequence(template)
        item.is_demo = template.is_demo
        item.created_by = actor
        item.updated_by = actor
        item.save()
        MaintenanceDueService.recalculate_template(template)
        return item

    @staticmethod
    def update(*, actor, item: MaintenanceTemplateItem, validated_data: dict):
        for field, value in validated_data.items():
            setattr(item, field, value)
        item.updated_by = actor
        item.save()
        MaintenanceDueService.recalculate_template(item.template)
        return item

    @staticmethod
    def delete(*, actor, item: MaintenanceTemplateItem):
        template = item.template
        item.updated_by = actor
        item.delete()
        MaintenanceDue.objects.filter(template_item=item).delete()
        MaintenanceDueService.recalculate_template(template)

    @staticmethod
    def reorder(*, actor, template: MaintenanceTemplate, item_ids: list):
        items = {
            str(item.id): item
            for item in MaintenanceTemplateItem.objects.filter(template=template)
        }
        for index, item_id in enumerate(item_ids, start=1):
            item = items.get(str(item_id))
            if item is None:
                continue
            item.sequence = index
            item.updated_by = actor
            item.save(update_fields=["sequence", "updated_by", "updated_at"])
        return list(MaintenanceTemplateItem.objects.filter(template=template).order_by("sequence"))


class MaintenanceDueService:
    @classmethod
    def recalculate_template(cls, template: MaintenanceTemplate) -> None:
        for uav in UAV.objects.filter(maintenance_template=template):
            cls.recalculate(uav)

    @classmethod
    def recalculate(cls, uav: UAV) -> list[MaintenanceDue]:
        now = timezone.now()
        rules = DueRulesService.get()
        template = uav.maintenance_template
        keep_ids: list = []
        if template is None:
            MaintenanceDue.objects.filter(uav=uav).delete()
            return []

        items = list(template.items.select_related("component_type"))
        components = list(
            UAVComponent.objects.filter(uav=uav, status=ComponentStatus.INSTALLED).select_related(
                "component_type"
            )
        )
        by_type: dict = {}
        for component in components:
            by_type.setdefault(component.component_type_id, []).append(component)

        changes: list[tuple] = []
        for item in items:
            for component in by_type.get(item.component_type_id, []):
                due, old_status = cls._upsert(uav, component, item, rules, now)
                keep_ids.append(due.id)
                changes.append((due, old_status, uav, component, item))

        MaintenanceDue.objects.filter(uav=uav).exclude(id__in=keep_ids).delete()
        dues = list(
            MaintenanceDue.objects.filter(uav=uav)
            .select_related("component", "template_item", "component__component_type")
            .order_by("-usage_percent", "template_item__sequence")
        )
        from apps.maintenance.work_order_services import WorkOrderService
        from apps.notifications.services import NotificationService

        NotificationService.emit_due_changes(changes)
        WorkOrderService.sync_auto_create(uav, dues)
        return dues

    @classmethod
    def _upsert(cls, uav, component, item, rules, now) -> tuple[MaintenanceDue, str | None]:
        used, due_at = cls._usage(uav, component, item, now)
        interval = item.interval_value
        usage_percent = (used / interval * Decimal("100")).quantize(Decimal("0.01"))
        remaining = (interval - used).quantize(Decimal("0.01"))
        status = cls._status(usage_percent, rules)
        existing = (
            MaintenanceDue.objects.filter(component=component, template_item=item)
            .only("status")
            .first()
        )
        old_status = existing.status if existing else None
        defaults = {
            "uav": uav,
            "status": status,
            "remaining_value": remaining,
            "remaining_unit": item.interval_unit,
            "usage_percent": usage_percent,
            "due_at": due_at,
            "calculated_at": now,
            "priority": item.priority,
        }
        due, _ = MaintenanceDue.objects.update_or_create(
            component=component,
            template_item=item,
            defaults=defaults,
        )
        return due, old_status

    @staticmethod
    def _status(usage_percent: Decimal, rules: dict[str, Decimal]) -> str:
        if usage_percent < rules["approaching_percent"]:
            return DueStatus.NORMAL
        if usage_percent < rules["due_percent"]:
            return DueStatus.APPROACHING
        if usage_percent < rules["overdue_percent"]:
            return DueStatus.DUE
        if usage_percent < rules["critical_percent"]:
            return DueStatus.OVERDUE
        return DueStatus.CRITICAL

    @classmethod
    def _usage(cls, uav, component, item, now) -> tuple[Decimal, datetime | None]:
        unit = item.interval_unit
        record = cls._latest_record(component, item)
        if unit == IntervalUnit.FLIGHT_HOURS:
            baseline = Decimal(record.operating_hours_snapshot) if record else Decimal("0")
            used = Decimal(component.operating_hours) - baseline
            return max(used, Decimal("0")), None
        if unit == IntervalUnit.FLIGHT_CYCLES:
            baseline = Decimal(record.uav_cycles_snapshot) if record else Decimal("0")
            used = Decimal(uav.total_flight_cycles) - baseline
            return max(used, Decimal("0")), None
        if unit == IntervalUnit.COMPONENT_CYCLES:
            baseline = Decimal(record.cycle_count_snapshot) if record else Decimal("0")
            used = Decimal(component.cycle_count) - baseline
            return max(used, Decimal("0")), None

        baseline_dt = cls._as_datetime(
            (record.performed_at if record else None)
            or component.last_maintenance_at
            or component.installed_at
            or uav.inventory_entry_date
        )
        if baseline_dt is None:
            return Decimal("0"), None

        elapsed_days = Decimal(str((now - baseline_dt).total_seconds() / 86400))
        if unit == IntervalUnit.CALENDAR_DAYS:
            due_at = baseline_dt + timedelta(days=float(item.interval_value))
            return elapsed_days, due_at
        if unit == IntervalUnit.CALENDAR_MONTHS:
            due_at = baseline_dt + timedelta(days=float(item.interval_value * DAYS_PER_MONTH))
            return (elapsed_days / DAYS_PER_MONTH), due_at
        if unit == IntervalUnit.CALENDAR_YEARS:
            due_at = baseline_dt + timedelta(days=float(item.interval_value * DAYS_PER_YEAR))
            return (elapsed_days / DAYS_PER_YEAR), due_at
        return Decimal("0"), None

    @staticmethod
    def _latest_record(component, item) -> MaintenanceRecord | None:
        if component is None or item is None:
            return None
        return (
            MaintenanceRecord.objects.filter(
                component=component,
                work_order__template_item=item,
            )
            .order_by("-performed_at")
            .first()
        )

    @staticmethod
    def _as_datetime(value) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            if timezone.is_naive(value):
                return timezone.make_aware(value)
            return value
        if isinstance(value, date):
            return timezone.make_aware(datetime.combine(value, time.min))
        return None
