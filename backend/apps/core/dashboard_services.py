from __future__ import annotations

from django.core.cache import cache
from django.db.models import Count, QuerySet

from apps.maintenance.enums import (
    ALERT_DUE_STATUSES,
    OPEN_WORK_ORDER_STATUSES,
    DueStatus,
    WorkOrderStatus,
)
from apps.maintenance.models import MaintenanceDue, WorkOrder
from apps.maintenance.serializers import MaintenanceDueSerializer, WorkOrderSerializer
from apps.reliability.enums import ReliabilityScope
from apps.reliability.services import ReliabilityService
from apps.uavs.enums import UAVStatus
from apps.uavs.models import UAV

ITEM_LIMIT = 8
CACHE_SECONDS = 45
ATTENTION_DUE_STATUSES = (DueStatus.DUE, DueStatus.OVERDUE, DueStatus.CRITICAL)
OVERDUE_DUE_STATUSES = (DueStatus.OVERDUE, DueStatus.CRITICAL)
ALL_WORK_ORDER_STATUSES = tuple(WorkOrderStatus.values)


def _count_map(queryset: QuerySet, field: str, keys: tuple[str, ...]) -> dict[str, int]:
    counts = {key: 0 for key in keys}
    for row in queryset.values(field).annotate(total=Count("id")):
        key = row[field]
        if key in counts:
            counts[key] = row["total"]
    return counts


class DashboardService:
    @classmethod
    def build(cls, *, user) -> dict:
        role = getattr(getattr(user, "role", None), "code", "") or ""
        cache_key = f"dashboard:{user.pk}:{role}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        data = cls._compute(user=user)
        cache.set(cache_key, data, CACHE_SECONDS)
        return data

    @classmethod
    def _compute(cls, *, user) -> dict:
        fleet = _count_map(UAV.objects.all(), "status", tuple(UAVStatus.values))
        dues = MaintenanceDue.objects.filter(status__in=ALERT_DUE_STATUSES)
        due_counts = _count_map(dues, "status", ALERT_DUE_STATUSES)
        due_items = dues.select_related(
            "uav",
            "component",
            "component__component_type",
            "template_item",
        ).order_by("-usage_percent", "template_item__sequence")[:ITEM_LIMIT]
        overdue_items = dues.filter(status__in=OVERDUE_DUE_STATUSES).select_related(
            "uav",
            "component",
            "component__component_type",
            "template_item",
        ).order_by("-usage_percent", "template_item__sequence")[:ITEM_LIMIT]
        work_orders = WorkOrder.objects.all()
        role = getattr(getattr(user, "role", None), "code", "")
        if role == "TECHNICIAN":
            work_orders = work_orders.filter(assigned_technician__user=user)
        wo_counts = _count_map(work_orders, "status", ALL_WORK_ORDER_STATUSES)
        open_count = sum(wo_counts[status] for status in OPEN_WORK_ORDER_STATUSES)
        wo_items = work_orders.filter(status__in=OPEN_WORK_ORDER_STATUSES).select_related(
            "uav",
            "component",
            "component__component_type",
            "template_item",
            "assigned_technician",
            "assigned_technician__user",
        ).order_by("-created_at")[:ITEM_LIMIT]
        reliability = ReliabilityService.compute(scope=ReliabilityScope.FLEET)
        return {
            "fleet": {
                **fleet,
                "total": sum(fleet.values()),
            },
            "dues": {
                "counts": {
                    **due_counts,
                    "attention": sum(due_counts[status] for status in ATTENTION_DUE_STATUSES),
                    "overdue": sum(due_counts[status] for status in OVERDUE_DUE_STATUSES),
                },
                "items": MaintenanceDueSerializer(due_items, many=True).data,
                "overdue_items": MaintenanceDueSerializer(overdue_items, many=True).data,
            },
            "work_orders": {
                "counts": {
                    **wo_counts,
                    "open": open_count,
                },
                "items": WorkOrderSerializer(wo_items, many=True).data,
            },
            "reliability": {
                "mtbf_hours": reliability["mtbf_hours"],
                "mttr_hours": reliability["mttr_hours"],
                "availability": reliability["availability"],
                "failure_count": reliability["failure_count"],
                "is_lower_bound": reliability["is_lower_bound"],
            },
        }
