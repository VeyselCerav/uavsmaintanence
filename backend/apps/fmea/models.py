from django.db import models
from django.db.models import Q

from apps.core.models import SoftDeleteModel
from apps.fmea.enums import FMEAStatus


class FMEA(SoftDeleteModel):
    code = models.CharField(max_length=64)
    title = models.CharField(max_length=255)
    uav_class = models.ForeignKey(
        "uavs.UAVClass",
        on_delete=models.PROTECT,
        related_name="fmea_analyses",
    )
    platform_type = models.ForeignKey(
        "uavs.PlatformType",
        on_delete=models.PROTECT,
        related_name="fmea_analyses",
    )
    component_type = models.ForeignKey(
        "components.ComponentType",
        on_delete=models.PROTECT,
        related_name="fmea_analyses",
    )
    mission_type = models.ForeignKey(
        "uavs.MissionType",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="fmea_analyses",
    )
    status = models.CharField(
        max_length=16,
        choices=FMEAStatus.choices,
        default=FMEAStatus.DRAFT,
    )
    revision = models.PositiveIntegerField(default=0)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_fmeas",
    )
    notes = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "fmea"
        indexes = [
            models.Index(fields=["uav_class", "platform_type", "component_type", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=Q(is_deleted=False),
                name="uniq_fmea_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.code


class FMEAItem(SoftDeleteModel):
    fmea = models.ForeignKey(FMEA, on_delete=models.CASCADE, related_name="items")
    sequence = models.PositiveIntegerField(default=1)
    function = models.CharField(max_length=255)
    functional_failure = models.CharField(max_length=255)
    failure_mode = models.TextField()
    catalog_mode = models.ForeignKey(
        "failures.FailureMode",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fmea_items",
    )
    failure_cause = models.TextField(blank=True)
    failure_effect = models.TextField(blank=True)
    severity = models.PositiveSmallIntegerField()
    occurrence = models.PositiveSmallIntegerField()
    detection = models.PositiveSmallIntegerField()
    rpn = models.PositiveIntegerField(default=0)
    existing_control = models.TextField(blank=True)
    recommended_action = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "fmea_item"
        ordering = ("sequence", "created_at")
        indexes = [
            models.Index(fields=["fmea", "sequence"]),
        ]

    def __str__(self) -> str:
        return f"{self.fmea_id}:{self.sequence}"
