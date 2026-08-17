from rest_framework import serializers

from apps.core.api_exceptions import InvalidDueRules
from apps.maintenance.models import (
    MaintenanceDue,
    MaintenanceRecord,
    MaintenanceTemplate,
    MaintenanceTemplateItem,
    WorkOrder,
)


class MaintenanceTemplateItemSerializer(serializers.ModelSerializer):
    component_type_code = serializers.CharField(source="component_type.code", read_only=True)
    component_type_name = serializers.CharField(source="component_type.name", read_only=True)

    class Meta:
        model = MaintenanceTemplateItem
        fields = (
            "id",
            "template",
            "component_type",
            "component_type_code",
            "component_type_name",
            "sequence",
            "task_code",
            "task_name",
            "interval_value",
            "interval_unit",
            "priority",
            "estimated_duration_minutes",
            "inspection_type",
            "rcm_strategy",
            "notes",
            "is_demo",
        )
        read_only_fields = ("template", "is_demo")


class MaintenanceTemplateSerializer(serializers.ModelSerializer):
    uav_class_code = serializers.CharField(source="uav_class.code", read_only=True)
    uav_class_name = serializers.CharField(source="uav_class.name", read_only=True)
    platform_code = serializers.CharField(source="platform_type.code", read_only=True)
    platform_name = serializers.CharField(source="platform_type.name", read_only=True)
    mission_code = serializers.CharField(source="mission_type.code", read_only=True)
    mission_name = serializers.CharField(source="mission_type.name", read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    items = MaintenanceTemplateItemSerializer(many=True, read_only=True)

    class Meta:
        model = MaintenanceTemplate
        fields = (
            "id",
            "code",
            "name",
            "description",
            "uav_class",
            "uav_class_code",
            "uav_class_name",
            "platform_type",
            "platform_code",
            "platform_name",
            "mission_type",
            "mission_code",
            "mission_name",
            "approach",
            "is_active",
            "is_demo",
            "notes",
            "item_count",
            "items",
        )


class MaintenanceDueSerializer(serializers.ModelSerializer):
    task_code = serializers.CharField(source="template_item.task_code", read_only=True)
    task_name = serializers.CharField(source="template_item.task_name", read_only=True)
    interval_value = serializers.DecimalField(
        source="template_item.interval_value",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    interval_unit = serializers.CharField(source="template_item.interval_unit", read_only=True)
    inspection_type = serializers.CharField(source="template_item.inspection_type", read_only=True)
    component_name = serializers.CharField(source="component.name", read_only=True)
    component_serial = serializers.CharField(source="component.serial_number", read_only=True)
    component_type_code = serializers.CharField(
        source="component.component_type.code",
        read_only=True,
    )
    component_type_name = serializers.CharField(
        source="component.component_type.name",
        read_only=True,
    )
    uav_registration = serializers.CharField(source="uav.registration_number", read_only=True)

    class Meta:
        model = MaintenanceDue
        fields = (
            "id",
            "uav",
            "uav_registration",
            "component",
            "component_name",
            "component_serial",
            "component_type_code",
            "component_type_name",
            "template_item",
            "task_code",
            "task_name",
            "interval_value",
            "interval_unit",
            "inspection_type",
            "status",
            "remaining_value",
            "remaining_unit",
            "usage_percent",
            "due_at",
            "calculated_at",
            "priority",
        )


class WorkOrderSerializer(serializers.ModelSerializer):
    uav_registration = serializers.CharField(source="uav.registration_number", read_only=True)
    component_name = serializers.CharField(source="component.name", read_only=True, allow_null=True)
    component_serial = serializers.CharField(
        source="component.serial_number",
        read_only=True,
        allow_null=True,
    )
    task_code = serializers.CharField(
        source="template_item.task_code",
        read_only=True,
        allow_null=True,
    )
    task_name = serializers.CharField(
        source="template_item.task_name",
        read_only=True,
        allow_null=True,
    )
    assigned_name = serializers.CharField(
        source="assigned_technician.user.full_name",
        read_only=True,
        allow_null=True,
    )
    due = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = WorkOrder
        fields = (
            "id",
            "number",
            "uav",
            "uav_registration",
            "component",
            "component_name",
            "component_serial",
            "template_item",
            "task_code",
            "task_name",
            "maintenance_type",
            "priority",
            "status",
            "planned_at",
            "started_at",
            "completed_at",
            "assigned_technician",
            "assigned_name",
            "estimated_duration_minutes",
            "actual_duration_minutes",
            "findings",
            "notes",
            "is_demo",
            "due",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("number", "status", "started_at", "completed_at", "is_demo")
        extra_kwargs = {
            "component": {"required": False, "allow_null": True},
            "template_item": {"required": False, "allow_null": True},
            "assigned_technician": {"required": False, "allow_null": True},
        }


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    work_order_number = serializers.CharField(source="work_order.number", read_only=True)
    uav_registration = serializers.CharField(source="uav.registration_number", read_only=True)
    component_name = serializers.CharField(source="component.name", read_only=True, allow_null=True)
    component_serial = serializers.CharField(
        source="component.serial_number",
        read_only=True,
        allow_null=True,
    )
    technician_name = serializers.CharField(
        source="technician.full_name",
        read_only=True,
        allow_null=True,
    )
    task_code = serializers.CharField(
        source="work_order.template_item.task_code",
        read_only=True,
        allow_null=True,
    )
    task_name = serializers.CharField(
        source="work_order.template_item.task_name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = MaintenanceRecord
        fields = (
            "id",
            "work_order",
            "work_order_number",
            "uav",
            "uav_registration",
            "component",
            "component_name",
            "component_serial",
            "maintenance_type",
            "performed_at",
            "technician",
            "technician_name",
            "description",
            "findings",
            "approach",
            "operating_hours_snapshot",
            "cycle_count_snapshot",
            "uav_cycles_snapshot",
            "task_code",
            "task_name",
            "created_at",
        )


class DueRulesSerializer(serializers.Serializer):
    approaching_percent = serializers.FloatField(min_value=0.01, max_value=10000)
    due_percent = serializers.FloatField(min_value=0.01, max_value=10000)
    overdue_percent = serializers.FloatField(min_value=0.01, max_value=10000)
    critical_percent = serializers.FloatField(min_value=0.01, max_value=10000)
    auto_create_on_due = serializers.BooleanField()

    def validate(self, attrs):
        sequence = (
            attrs["approaching_percent"],
            attrs["due_percent"],
            attrs["overdue_percent"],
            attrs["critical_percent"],
        )
        if not (sequence[0] < sequence[1] < sequence[2] < sequence[3]):
            raise InvalidDueRules()
        return attrs


