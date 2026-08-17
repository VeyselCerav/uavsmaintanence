from __future__ import annotations

from django.db import IntegrityError
from django.utils import timezone

from apps.accounts.models import User
from apps.maintenance.enums import DueStatus
from apps.notifications.enums import NotificationType
from apps.notifications.models import Notification

ALERT_TYPE_MAP = {
    DueStatus.DUE: NotificationType.MAINTENANCE_DUE,
    DueStatus.OVERDUE: NotificationType.MAINTENANCE_OVERDUE,
    DueStatus.CRITICAL: NotificationType.CRITICAL_COMPONENT,
}

RECIPIENT_ROLES = ("ADMIN", "MAINTENANCE_MANAGER")


class NotificationService:
    @staticmethod
    def recipients():
        return User.objects.filter(is_active=True, role__code__in=RECIPIENT_ROLES)

    @classmethod
    def emit_due_changes(cls, changes: list[tuple]) -> None:
        recipients = list(cls.recipients())
        if not recipients:
            return
        for due, old_status, uav, component, item in changes:
            new_status = due.status
            if new_status not in ALERT_TYPE_MAP or old_status == new_status:
                continue
            ntype = ALERT_TYPE_MAP[new_status]
            payload = {
                "due_id": str(due.id),
                "uav_id": str(uav.id),
                "uav_registration": uav.registration_number,
                "task_code": item.task_code,
                "task_name": item.task_name,
                "status": new_status,
                "usage_percent": str(due.usage_percent),
                "component_serial": getattr(component, "serial_number", ""),
            }
            for user in recipients:
                cls.create_unread(
                    user=user,
                    ntype=ntype,
                    source_id=str(due.id),
                    payload=payload,
                )

    @classmethod
    def emit_work_order_assigned(cls, work_order) -> None:
        technician = getattr(work_order, "assigned_technician", None)
        user = getattr(technician, "user", None) if technician is not None else None
        if user is None or not user.is_active:
            return
        cls.create_unread(
            user=user,
            ntype=NotificationType.WORK_ORDER_ASSIGNED,
            source_id=str(work_order.id),
            payload=cls.work_order_payload(work_order),
        )

    @classmethod
    def emit_work_order_completed(cls, work_order) -> None:
        for user in cls.recipients():
            cls.create_unread(
                user=user,
                ntype=NotificationType.WORK_ORDER_COMPLETED,
                source_id=str(work_order.id),
                payload=cls.work_order_payload(work_order),
            )

    @staticmethod
    def work_order_payload(work_order) -> dict:
        item = work_order.template_item
        uav = work_order.uav
        technician = getattr(work_order, "assigned_technician", None)
        assigned_user = getattr(technician, "user", None) if technician is not None else None
        return {
            "work_order_id": str(work_order.id),
            "work_order_number": work_order.number,
            "uav_id": str(work_order.uav_id) if work_order.uav_id else "",
            "uav_registration": getattr(uav, "registration_number", ""),
            "task_code": getattr(item, "task_code", "") or "",
            "task_name": getattr(item, "task_name", "") or "",
            "assigned_name": getattr(assigned_user, "full_name", "") or "",
        }

    @staticmethod
    def create_unread(*, user, ntype: str, source_id: str, payload: dict) -> Notification | None:
        if Notification.objects.filter(
            user=user,
            type=ntype,
            source_id=source_id,
            is_read=False,
        ).exists():
            return None
        try:
            return Notification.objects.create(
                user=user,
                type=ntype,
                source_id=source_id,
                title_key=f"notifications.titles.{ntype}",
                body_key=f"notifications.bodies.{ntype}",
                payload=payload,
            )
        except IntegrityError:
            return None

    @staticmethod
    def mark_read(*, notification: Notification) -> Notification:
        if notification.is_read:
            return notification
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at", "updated_at"])
        return notification

    @staticmethod
    def mark_all_read(*, user) -> int:
        return Notification.objects.filter(user=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now(),
        )
