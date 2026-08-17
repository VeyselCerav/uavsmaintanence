from decimal import Decimal

from rest_framework import serializers

from apps.parts.models import CostRecord, Part, PartCompatibility, WorkOrderPart


class PartCompatibilitySerializer(serializers.ModelSerializer):
    uav_class_code = serializers.CharField(source="uav_class.code", read_only=True, default="")
    uav_class_name = serializers.CharField(source="uav_class.name", read_only=True, default="")
    platform_code = serializers.CharField(source="platform_type.code", read_only=True, default="")
    platform_name = serializers.CharField(source="platform_type.name", read_only=True, default="")
    component_type_code = serializers.CharField(source="component_type.code", read_only=True)
    component_type_name = serializers.CharField(source="component_type.name", read_only=True)

    class Meta:
        model = PartCompatibility
        fields = (
            "id",
            "part",
            "uav_class",
            "uav_class_code",
            "uav_class_name",
            "platform_type",
            "platform_code",
            "platform_name",
            "component_type",
            "component_type_code",
            "component_type_name",
            "is_demo",
            "created_at",
        )
        read_only_fields = ("part", "is_demo")
        extra_kwargs = {
            "uav_class": {"required": False, "allow_null": True},
            "platform_type": {"required": False, "allow_null": True},
        }


class PartSerializer(serializers.ModelSerializer):
    stock_low = serializers.SerializerMethodField()
    compatibilities = PartCompatibilitySerializer(many=True, read_only=True)

    class Meta:
        model = Part
        fields = (
            "id",
            "part_number",
            "name",
            "manufacturer",
            "model",
            "stock_qty",
            "min_stock_qty",
            "unit_cost",
            "currency",
            "supplier",
            "location",
            "status",
            "notes",
            "stock_low",
            "is_demo",
            "compatibilities",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("is_demo",)

    def get_stock_low(self, obj) -> bool:
        return obj.stock_qty < obj.min_stock_qty


class CostRecordSerializer(serializers.ModelSerializer):
    uav_registration = serializers.CharField(source="uav.registration_number", read_only=True)
    work_order_number = serializers.CharField(
        source="work_order.number",
        read_only=True,
        default="",
    )
    component_name = serializers.CharField(source="component.name", read_only=True, default="")

    class Meta:
        model = CostRecord
        fields = (
            "id",
            "work_order",
            "work_order_number",
            "uav",
            "uav_registration",
            "component",
            "component_name",
            "maintenance_type",
            "part_cost",
            "labor_cost",
            "other_cost",
            "total_cost",
            "currency",
            "occurred_at",
            "notes",
            "is_demo",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("total_cost", "is_demo")
        extra_kwargs = {
            "work_order": {"required": False, "allow_null": True},
            "component": {"required": False, "allow_null": True},
            "maintenance_type": {"required": False, "allow_blank": True},
            "part_cost": {"required": False},
            "labor_cost": {"required": False},
            "other_cost": {"required": False},
            "occurred_at": {"required": False},
        }


class WorkOrderPartSerializer(serializers.ModelSerializer):
    part_number = serializers.CharField(source="part.part_number", read_only=True)
    part_name = serializers.CharField(source="part.name", read_only=True)
    currency = serializers.CharField(source="part.currency", read_only=True)
    line_cost = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrderPart
        fields = (
            "id",
            "work_order",
            "part",
            "part_number",
            "part_name",
            "quantity",
            "unit_cost",
            "currency",
            "line_cost",
            "created_at",
        )
        read_only_fields = ("work_order", "unit_cost")
        extra_kwargs = {"unit_cost": {"required": False}}

    def get_line_cost(self, obj):
        return format((obj.quantity * obj.unit_cost).quantize(Decimal("0.01")), "f")
