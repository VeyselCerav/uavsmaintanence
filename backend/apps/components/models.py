from django.db import models
from django.db.models import Q

from apps.components.enums import ComponentStatus
from apps.core.models import SoftDeleteModel


class ComponentType(SoftDeleteModel):
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    tracks_hours = models.BooleanField(default=True)
    tracks_cycles = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "component_type"
        ordering = ("code",)
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=Q(is_deleted=False),
                name="uniq_component_type_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.code


class UAVComponent(SoftDeleteModel):
    uav = models.ForeignKey("uavs.UAV", on_delete=models.PROTECT, related_name="components")
    component_type = models.ForeignKey(
        ComponentType,
        on_delete=models.PROTECT,
        related_name="installed_components",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    name = models.CharField(max_length=128)
    serial_number = models.CharField(max_length=128, blank=True)
    part_number = models.CharField(max_length=128, blank=True)
    manufacturer = models.CharField(max_length=128, blank=True)
    model = models.CharField(max_length=128, blank=True)
    installed_at = models.DateTimeField(null=True, blank=True)
    removed_at = models.DateTimeField(null=True, blank=True)
    operating_hours = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cycle_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=32,
        choices=ComponentStatus.choices,
        default=ComponentStatus.INSTALLED,
    )
    last_maintenance_at = models.DateTimeField(null=True, blank=True)
    next_maintenance_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "uav_component"
        indexes = [
            models.Index(fields=["uav", "status"]),
            models.Index(fields=["component_type"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["serial_number"],
                condition=Q(
                    is_deleted=False,
                    removed_at__isnull=True,
                )
                & ~Q(serial_number=""),
                name="uniq_component_serial_installed",
            ),
        ]

    def __str__(self) -> str:
        return self.serial_number or self.name
