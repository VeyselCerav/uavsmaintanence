from __future__ import annotations

from decimal import Decimal

from django.db.models import Count, QuerySet, Sum

from apps.core.api_exceptions import InvalidReliabilityRange
from apps.maintenance.enums import (
    ALERT_DUE_STATUSES,
    OPEN_WORK_ORDER_STATUSES,
    DueStatus,
    WorkOrderStatus,
)
from apps.maintenance.models import MaintenanceDue, MaintenanceTemplateItem, WorkOrder
from apps.parts.models import CostRecord
from apps.reliability.services import ReliabilityService, _parse_bound
from apps.uavs.enums import MaintenanceApproach
from apps.uavs.models import UAV

COST_PLACES = Decimal("0.01")
ALL_DUE_STATUSES = tuple(DueStatus.values)
ALL_WORK_ORDER_STATUSES = tuple(WorkOrderStatus.values)
ATTENTION_DUE_STATUSES = (DueStatus.DUE, DueStatus.OVERDUE, DueStatus.CRITICAL)
OVERDUE_DUE_STATUSES = (DueStatus.OVERDUE, DueStatus.CRITICAL)


def _count_map(queryset: QuerySet, field: str, keys: tuple[str, ...]) -> dict[str, int]:
    counts = {key: 0 for key in keys}
    for row in queryset.values(field).annotate(total=Count("id")):
        key = row[field]
        if key in counts:
            counts[key] = row["total"]
    return counts


class ApproachComparisonService:
    @classmethod
    def compare(
        cls,
        *,
        class_id: str | None = None,
        platform_id: str | None = None,
        mission_id: str | None = None,
        period_start: str | None = None,
        period_end: str | None = None,
    ) -> dict:
        start = _parse_bound(period_start, end=False)
        end = _parse_bound(period_end, end=True)
        if start and end and start > end:
            raise InvalidReliabilityRange()

        uavs = UAV.objects.select_related(
            "uav_class",
            "platform_type",
            "mission_type",
            "maintenance_template",
        )
        if class_id:
            uavs = uavs.filter(uav_class_id=class_id)
        if platform_id:
            uavs = uavs.filter(platform_type_id=platform_id)
        if mission_id:
            uavs = uavs.filter(mission_type_id=mission_id)

        arms = [
            cls._arm(approach, uavs.filter(maintenance_approach=approach), start=start, end=end)
            for approach in MaintenanceApproach.values
        ]
        return {
            "filters": {
                "uav_class_id": class_id or None,
                "platform_type_id": platform_id or None,
                "mission_type_id": mission_id or None,
                "period_start": start.isoformat() if start else None,
                "period_end": end.isoformat() if end else None,
            },
            "is_demo": uavs.filter(is_demo=True).exists(),
            "arms": arms,
        }

    @classmethod
    def _arm(cls, approach: str, uavs: QuerySet, *, start, end) -> dict:
        uav_ids = list(uavs.values_list("id", flat=True))
        template_ids = list(
            uavs.exclude(maintenance_template_id=None)
            .values_list("maintenance_template_id", flat=True)
            .distinct()
        )
        dues = MaintenanceDue.objects.filter(uav_id__in=uav_ids)
        due_counts = _count_map(dues, "status", ALL_DUE_STATUSES)
        work_orders = WorkOrder.objects.filter(uav_id__in=uav_ids)
        if start:
            work_orders = work_orders.filter(created_at__gte=start)
        if end:
            work_orders = work_orders.filter(created_at__lte=end)
        wo_counts = _count_map(work_orders, "status", ALL_WORK_ORDER_STATUSES)
        costs = CostRecord.objects.filter(uav_id__in=uav_ids)
        if start:
            costs = costs.filter(occurred_at__gte=start)
        if end:
            costs = costs.filter(occurred_at__lte=end)
        cost_total = costs.aggregate(total=Sum("total_cost")).get("total") or Decimal("0")
        reliability = ReliabilityService.metrics_for_uavs(uavs, start=start, end=end)
        return {
            "approach": approach,
            "uav_count": len(uav_ids),
            "template_count": len(template_ids),
            "template_item_count": MaintenanceTemplateItem.objects.filter(
                template_id__in=template_ids,
            ).count(),
            "due_counts": due_counts,
            "due_attention": sum(due_counts[status] for status in ATTENTION_DUE_STATUSES),
            "due_overdue": sum(due_counts[status] for status in OVERDUE_DUE_STATUSES),
            "due_alert": sum(due_counts[status] for status in ALERT_DUE_STATUSES),
            "work_order_counts": wo_counts,
            "work_order_open": sum(wo_counts[status] for status in OPEN_WORK_ORDER_STATUSES),
            "cost_total": format(cost_total.quantize(COST_PLACES), "f"),
            "uavs": list(
                uavs.order_by("registration_number").values("id", "registration_number")[:20]
            ),
            **reliability,
        }
