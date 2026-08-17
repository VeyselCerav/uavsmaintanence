from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel
from apps.notifications.enums import NotificationType


class Notification(TimeStampedModel):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=64, choices=NotificationType.choices)
    title_key = models.CharField(max_length=128)
    body_key = models.CharField(max_length=128)
    payload = models.JSONField(default=dict)
    source_id = models.CharField(max_length=64, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notification"
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "-created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "type", "source_id"],
                condition=Q(is_read=False),
                name="uniq_unread_notification_source",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.type}"
