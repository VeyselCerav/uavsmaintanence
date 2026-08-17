from django.db import models
from django.db.models import Q

from apps.core.models import SoftDeleteModel
from apps.uavs.enums import MaintenanceApproach, UAVStatus


class UAVClass(SoftDeleteModel):
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    mtow_min_kg = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    mtow_max_kg = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_demo = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "uav_class"
        ordering = ("sort_order", "code")
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=Q(is_deleted=False),
                name="uniq_uav_class_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.code


class PlatformType(SoftDeleteModel):
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "platform_type"
        ordering = ("code",)
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=Q(is_deleted=False),
                name="uniq_platform_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.code


class MissionType(SoftDeleteModel):
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "mission_type"
        ordering = ("code",)
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=Q(is_deleted=False),
                name="uniq_mission_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.code


class UAV(SoftDeleteModel):
    registration_number = models.CharField(max_length=64)
    serial_number = models.CharField(max_length=128)
    manufacturer = models.CharField(max_length=128)
    model = models.CharField(max_length=128)
    uav_class = models.ForeignKey(UAVClass, on_delete=models.PROTECT, related_name="uavs")
    platform_type = models.ForeignKey(PlatformType, on_delete=models.PROTECT, related_name="uavs")
    mission_type = models.ForeignKey(MissionType, on_delete=models.PROTECT, related_name="uavs")
    maintenance_template = models.ForeignKey(
        "maintenance.MaintenanceTemplate",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uavs",
    )
    maintenance_approach = models.CharField(
        max_length=32,
        choices=MaintenanceApproach.choices,
        default=MaintenanceApproach.CLASS_SPECIFIC,
    )
    mtow_kg = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    production_date = models.DateField(null=True, blank=True)
    inventory_entry_date = models.DateField(null=True, blank=True)
    total_flight_hours = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_flight_count = models.PositiveIntegerField(default=0)
    total_flight_cycles = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=32, choices=UAVStatus.choices, default=UAVStatus.READY)
    notes = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "uav"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["uav_class", "platform_type", "mission_type"]),
            models.Index(fields=["maintenance_template"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["registration_number"],
                condition=Q(is_deleted=False),
                name="uniq_uav_registration_alive",
            ),
            models.UniqueConstraint(
                fields=["serial_number"],
                condition=Q(is_deleted=False),
                name="uniq_uav_serial_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.registration_number
