from django.db import models
from django.db.models import Q

from apps.core.models import SoftDeleteModel
from apps.maintenance.enums import RCMStrategy
from apps.rcm.enums import Detectability, RCMStatus


class RCMAnalysis(SoftDeleteModel):
    code = models.CharField(max_length=64)
    title = models.CharField(max_length=255)
    uav_class = models.ForeignKey(
        "uavs.UAVClass",
        on_delete=models.PROTECT,
        related_name="rcm_analyses",
    )
    platform_type = models.ForeignKey(
        "uavs.PlatformType",
        on_delete=models.PROTECT,
        related_name="rcm_analyses",
    )
    component_type = models.ForeignKey(
        "components.ComponentType",
        on_delete=models.PROTECT,
        related_name="rcm_analyses",
    )
    mission_type = models.ForeignKey(
        "uavs.MissionType",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="rcm_analyses",
    )
    status = models.CharField(
        max_length=16,
        choices=RCMStatus.choices,
        default=RCMStatus.DRAFT,
    )
    revision = models.PositiveIntegerField(default=0)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_rcms",
    )
    notes = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "rcm_analysis"
        indexes = [
            models.Index(fields=["uav_class", "platform_type", "component_type", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=Q(is_deleted=False),
                name="uniq_rcm_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.code


class RCMItem(SoftDeleteModel):
    analysis = models.ForeignKey(RCMAnalysis, on_delete=models.CASCADE, related_name="items")
    sequence = models.PositiveIntegerField(default=1)
    function = models.CharField(max_length=255)
    functional_failure = models.CharField(max_length=255)
    failure_mode = models.TextField()
    failure_effect = models.TextField(blank=True)
    safety_effect = models.BooleanField(default=False)
    operational_effect = models.BooleanField(default=False)
    detectability = models.CharField(
        max_length=16,
        choices=Detectability.choices,
        default=Detectability.MEDIUM,
    )
    preventive_feasible = models.BooleanField(default=True)
    suggested_strategy = models.CharField(max_length=32, choices=RCMStrategy.choices)
    strategy = models.CharField(max_length=32, choices=RCMStrategy.choices)
    is_overridden = models.BooleanField(default=False)
    rationale = models.TextField(blank=True)
    fmea_item = models.ForeignKey(
        "fmea.FMEAItem",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rcm_items",
    )
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "rcm_item"
        ordering = ("sequence", "created_at")
        indexes = [
            models.Index(fields=["analysis", "sequence"]),
        ]

    def __str__(self) -> str:
        return f"{self.analysis_id}:{self.sequence}"
