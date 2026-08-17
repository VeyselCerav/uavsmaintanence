from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.models import SoftDeleteModel, TimeStampedModel
from apps.maintenance.enums import (
    DueStatus,
    InspectionType,
    IntervalUnit,
    MaintenanceType,
    Priority,
    RCMStrategy,
    WorkOrderStatus,
)
from apps.uavs.enums import MaintenanceApproach


class MaintenanceTemplate(SoftDeleteModel):
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    uav_class = models.ForeignKey(
        "uavs.UAVClass",
        on_delete=models.PROTECT,
        related_name="maintenance_templates",
    )
    platform_type = models.ForeignKey(
        "uavs.PlatformType",
        on_delete=models.PROTECT,
        related_name="maintenance_templates",
    )
    mission_type = models.ForeignKey(
        "uavs.MissionType",
        on_delete=models.PROTECT,
        related_name="maintenance_templates",
    )
    approach = models.CharField(max_length=32, choices=MaintenanceApproach.choices)
    is_active = models.BooleanField(default=True)
    is_demo = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "maintenance_template"
        constraints = [
            models.UniqueConstraint(
                fields=["uav_class", "platform_type", "mission_type", "approach"],
                condition=Q(is_deleted=False, is_active=True),
                name="uniq_active_template_triple",
            ),
            models.UniqueConstraint(
                fields=["code"],
                condition=Q(is_deleted=False),
                name="uniq_template_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.code


class MaintenanceTemplateItem(SoftDeleteModel):
    template = models.ForeignKey(
        MaintenanceTemplate,
        on_delete=models.CASCADE,
        related_name="items",
    )
    component_type = models.ForeignKey(
        "components.ComponentType",
        on_delete=models.PROTECT,
        related_name="template_items",
    )
    sequence = models.PositiveIntegerField(default=0)
    task_code = models.CharField(max_length=64)
    task_name = models.CharField(max_length=255)
    interval_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    interval_unit = models.CharField(max_length=32, choices=IntervalUnit.choices)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.MEDIUM)
    estimated_duration_minutes = models.PositiveIntegerField(default=60)
    inspection_type = models.CharField(
        max_length=32,
        choices=InspectionType.choices,
        default=InspectionType.VISUAL,
    )
    rcm_strategy = models.CharField(
        max_length=32,
        choices=RCMStrategy.choices,
        default=RCMStrategy.SCHEDULED_INSPECTION,
    )
    notes = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "maintenance_template_item"
        ordering = ("sequence", "task_code")
        constraints = [
            models.UniqueConstraint(
                fields=["template", "component_type", "task_code"],
                condition=Q(is_deleted=False),
                name="uniq_template_item_task_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.task_code


class MaintenanceDue(TimeStampedModel):
    uav = models.ForeignKey("uavs.UAV", on_delete=models.CASCADE, related_name="maintenance_dues")
    component = models.ForeignKey(
        "components.UAVComponent",
        on_delete=models.CASCADE,
        related_name="maintenance_dues",
    )
    template_item = models.ForeignKey(
        MaintenanceTemplateItem,
        on_delete=models.CASCADE,
        related_name="dues",
    )
    status = models.CharField(max_length=16, choices=DueStatus.choices)
    remaining_value = models.DecimalField(max_digits=12, decimal_places=2)
    remaining_unit = models.CharField(max_length=32, choices=IntervalUnit.choices)
    usage_percent = models.DecimalField(max_digits=12, decimal_places=2)
    due_at = models.DateTimeField(null=True, blank=True)
    calculated_at = models.DateTimeField()
    priority = models.CharField(max_length=16, choices=Priority.choices)

    class Meta:
        db_table = "maintenance_due"
        constraints = [
            models.UniqueConstraint(
                fields=["component", "template_item"],
                name="uniq_due_component_item",
            ),
        ]
        indexes = [
            models.Index(fields=["uav", "status"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.uav_id}:{self.template_item_id}"


class WorkOrder(SoftDeleteModel):
    number = models.CharField(max_length=64)
    uav = models.ForeignKey("uavs.UAV", on_delete=models.PROTECT, related_name="work_orders")
    component = models.ForeignKey(
        "components.UAVComponent",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="work_orders",
    )
    template_item = models.ForeignKey(
        MaintenanceTemplateItem,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="work_orders",
    )
    maintenance_type = models.CharField(
        max_length=32,
        choices=MaintenanceType.choices,
        default=MaintenanceType.PREVENTIVE,
    )
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(
        max_length=32,
        choices=WorkOrderStatus.choices,
        default=WorkOrderStatus.OPEN,
    )
    planned_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_technician = models.ForeignKey(
        "technicians.Technician",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_work_orders",
    )
    estimated_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    actual_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    findings = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "work_order"
        indexes = [
            models.Index(fields=["uav", "status"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["number"],
                condition=Q(is_deleted=False),
                name="uniq_work_order_number_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.number


class MaintenanceRecord(TimeStampedModel):
    work_order = models.OneToOneField(
        WorkOrder,
        on_delete=models.PROTECT,
        related_name="record",
    )
    uav = models.ForeignKey(
        "uavs.UAV",
        on_delete=models.PROTECT,
        related_name="maintenance_records",
    )
    component = models.ForeignKey(
        "components.UAVComponent",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="maintenance_records",
    )
    maintenance_type = models.CharField(max_length=32, choices=MaintenanceType.choices)
    performed_at = models.DateTimeField()
    technician = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="maintenance_records",
    )
    description = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    action_taken = models.TextField(blank=True)
    labor_hours = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    result = models.CharField(max_length=64, blank=True)
    next_maintenance_at = models.DateTimeField(null=True, blank=True)
    approach = models.CharField(max_length=32, choices=MaintenanceApproach.choices)
    operating_hours_snapshot = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cycle_count_snapshot = models.PositiveIntegerField(default=0)
    uav_cycles_snapshot = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "maintenance_record"
        indexes = [
            models.Index(fields=["uav", "performed_at"]),
            models.Index(fields=["component", "performed_at"]),
        ]

    def __str__(self) -> str:
        return str(self.work_order_id)
