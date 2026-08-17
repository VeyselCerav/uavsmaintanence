from django.db import models
from django.db.models import Q

from apps.core.models import SoftDeleteModel
from apps.maintenance.enums import MaintenanceType
from apps.parts.enums import Currency, PartStatus


class Part(SoftDeleteModel):
    part_number = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    manufacturer = models.CharField(max_length=128, blank=True)
    model = models.CharField(max_length=128, blank=True)
    stock_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    min_stock_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, choices=Currency.choices, default=Currency.TRY)
    supplier = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=16, choices=PartStatus.choices, default=PartStatus.ACTIVE)
    notes = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "part"
        ordering = ("part_number",)
        constraints = [
            models.UniqueConstraint(
                fields=["part_number"],
                condition=Q(is_deleted=False),
                name="uniq_part_number_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.part_number


class PartCompatibility(SoftDeleteModel):
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name="compatibilities")
    uav_class = models.ForeignKey(
        "uavs.UAVClass",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="part_compatibilities",
    )
    platform_type = models.ForeignKey(
        "uavs.PlatformType",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="part_compatibilities",
    )
    component_type = models.ForeignKey(
        "components.ComponentType",
        on_delete=models.PROTECT,
        related_name="part_compatibilities",
    )
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "part_compatibility"
        indexes = [
            models.Index(fields=["part", "component_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.part_id}:{self.component_type_id}"


class CostRecord(SoftDeleteModel):
    work_order = models.ForeignKey(
        "maintenance.WorkOrder",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cost_records",
    )
    uav = models.ForeignKey("uavs.UAV", on_delete=models.PROTECT, related_name="cost_records")
    component = models.ForeignKey(
        "components.UAVComponent",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="cost_records",
    )
    maintenance_type = models.CharField(
        max_length=32,
        choices=MaintenanceType.choices,
        blank=True,
    )
    part_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, choices=Currency.choices, default=Currency.TRY)
    occurred_at = models.DateTimeField()
    notes = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "cost_record"
        indexes = [
            models.Index(fields=["uav", "-occurred_at"]),
            models.Index(fields=["work_order"]),
        ]

    def __str__(self) -> str:
        return str(self.uav_id)


class WorkOrderPart(SoftDeleteModel):
    work_order = models.ForeignKey(
        "maintenance.WorkOrder",
        on_delete=models.CASCADE,
        related_name="parts",
    )
    part = models.ForeignKey(Part, on_delete=models.PROTECT, related_name="work_order_parts")
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "work_order_part"
        constraints = [
            models.UniqueConstraint(
                fields=["work_order", "part"],
                condition=Q(is_deleted=False),
                name="uniq_work_order_part_alive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.work_order_id}:{self.part_id}"
