from __future__ import annotations

from django.db.models import Q

from apps.components.models import UAVComponent
from apps.core.permissions import user_has_permission
from apps.failures.models import Failure
from apps.maintenance.models import MaintenanceDue, MaintenanceRecord, WorkOrder
from apps.parts.models import Part
from apps.uavs.models import UAV

RESULT_LIMIT = 8
MIN_QUERY = 2


def _item(*, entity: str, id, title: str, subtitle: str, href: str) -> dict:
    return {
        "entity": entity,
        "id": str(id),
        "title": title,
        "subtitle": subtitle,
        "href": href,
    }


class SearchService:
    @classmethod
    def search(cls, *, user, query: str) -> dict:
        term = (query or "").strip()
        groups = []
        if len(term) < MIN_QUERY:
            return {"query": term, "groups": groups}

        if user_has_permission(user, "uav.view"):
            uavs = UAV.objects.filter(
                Q(registration_number__icontains=term)
                | Q(serial_number__icontains=term)
                | Q(model__icontains=term)
            ).order_by("registration_number")[:RESULT_LIMIT]
            items = [
                _item(
                    entity="uav",
                    id=uav.id,
                    title=uav.registration_number,
                    subtitle=uav.serial_number,
                    href=f"/uavs/{uav.id}",
                )
                for uav in uavs
            ]
            if items:
                groups.append({"entity": "uav", "items": items})

        if user_has_permission(user, "component.view"):
            components = UAVComponent.objects.select_related("uav").filter(
                Q(serial_number__icontains=term)
                | Q(name__icontains=term)
                | Q(part_number__icontains=term)
            ).order_by("serial_number")[:RESULT_LIMIT]
            items = [
                _item(
                    entity="component",
                    id=component.id,
                    title=component.serial_number or component.name,
                    subtitle=component.uav.registration_number,
                    href=f"/uavs/{component.uav_id}",
                )
                for component in components
            ]
            if items:
                groups.append({"entity": "component", "items": items})

        if user_has_permission(user, "work_order.view"):
            work_orders = WorkOrder.objects.select_related("uav").filter(
                Q(number__icontains=term) | Q(uav__registration_number__icontains=term)
            ).order_by("-created_at")[:RESULT_LIMIT]
            items = [
                _item(
                    entity="work_order",
                    id=order.id,
                    title=order.number,
                    subtitle=order.uav.registration_number,
                    href=f"/work-orders/{order.id}",
                )
                for order in work_orders
            ]
            if items:
                groups.append({"entity": "work_order", "items": items})

        if user_has_permission(user, "maintenance.view"):
            dues = MaintenanceDue.objects.select_related("uav", "template_item").filter(
                Q(template_item__task_code__icontains=term)
                | Q(template_item__task_name__icontains=term)
                | Q(uav__registration_number__icontains=term)
            ).order_by("-usage_percent")[:RESULT_LIMIT]
            due_items = [
                _item(
                    entity="maintenance",
                    id=due.id,
                    title=due.template_item.task_code if due.template_item_id else str(due.id),
                    subtitle=due.uav.registration_number,
                    href="/maintenance",
                )
                for due in dues
            ]
            records = MaintenanceRecord.objects.select_related("uav", "work_order").filter(
                Q(work_order__number__icontains=term)
                | Q(description__icontains=term)
                | Q(uav__registration_number__icontains=term)
            ).order_by("-performed_at")[:RESULT_LIMIT]
            record_items = [
                _item(
                    entity="maintenance",
                    id=record.id,
                    title=record.work_order.number if record.work_order_id else str(record.id),
                    subtitle=record.uav.registration_number,
                    href="/maintenance/records",
                )
                for record in records
            ]
            items = due_items + record_items
            if items:
                groups.append({"entity": "maintenance", "items": items[:RESULT_LIMIT]})

        if user_has_permission(user, "failure.view"):
            failures = Failure.objects.select_related("uav").filter(
                Q(description__icontains=term) | Q(uav__registration_number__icontains=term)
            ).order_by("-occurred_at")[:RESULT_LIMIT]
            items = [
                _item(
                    entity="failure",
                    id=failure.id,
                    title=failure.uav.registration_number,
                    subtitle=(failure.description or "")[:80],
                    href=f"/failures/{failure.id}",
                )
                for failure in failures
            ]
            if items:
                groups.append({"entity": "failure", "items": items})

        if user_has_permission(user, "part.view"):
            parts = Part.objects.filter(
                Q(part_number__icontains=term) | Q(name__icontains=term)
            ).order_by("part_number")[:RESULT_LIMIT]
            items = [
                _item(
                    entity="part",
                    id=part.id,
                    title=part.part_number,
                    subtitle=part.name,
                    href=f"/parts/{part.id}",
                )
                for part in parts
            ]
            if items:
                groups.append({"entity": "part", "items": items})

        return {"query": term, "groups": groups}
