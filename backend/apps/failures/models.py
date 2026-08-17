from django.db import models
from django.db.models import Q

from apps.core.models import SoftDeleteModel
from apps.failures.enums import DiscoveredDuring, FailureSeverity


class FailureMode(SoftDeleteModel):
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "failure_mode"
        ordering = ("code",)
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=Q(is_deleted=False),
                name="uniq_failure_mode_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.code


class Failure(SoftDeleteModel):
    uav = models.ForeignKey("uavs.UAV", on_delete=models.PROTECT, related_name="failures")
    component = models.ForeignKey(
        "components.UAVComponent",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="failures",
    )
    failure_mode = models.ForeignKey(
        FailureMode,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="failures",
    )
    occurred_at = models.DateTimeField()
    discovered_during = models.CharField(
        max_length=16,
        choices=DiscoveredDuring.choices,
        default=DiscoveredDuring.OTHER,
    )
    severity = models.CharField(
        max_length=16,
        choices=FailureSeverity.choices,
        default=FailureSeverity.MEDIUM,
    )
    description = models.TextField()
    downtime_hours = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    resolved_at = models.DateTimeField(null=True, blank=True)
    work_order = models.ForeignKey(
        "maintenance.WorkOrder",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="failures",
    )
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "failure"
        indexes = [
            models.Index(fields=["uav", "-occurred_at"]),
            models.Index(fields=["resolved_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.uav_id} {self.occurred_at}"
