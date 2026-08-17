from django.contrib import admin

from apps.parts.models import CostRecord, Part, PartCompatibility, WorkOrderPart


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ("part_number", "name", "stock_qty", "status", "is_demo")
    search_fields = ("part_number", "name")


@admin.register(PartCompatibility)
class PartCompatibilityAdmin(admin.ModelAdmin):
    list_display = ("part", "uav_class", "platform_type", "component_type")


@admin.register(CostRecord)
class CostRecordAdmin(admin.ModelAdmin):
    list_display = ("uav", "total_cost", "currency", "occurred_at")


@admin.register(WorkOrderPart)
class WorkOrderPartAdmin(admin.ModelAdmin):
    list_display = ("work_order", "part", "quantity", "unit_cost")
