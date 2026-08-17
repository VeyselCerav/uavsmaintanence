from rest_framework import serializers

from apps.rcm.models import RCMAnalysis, RCMItem
from apps.rcm.services import RCMEvaluationService


class RCMItemSerializer(serializers.ModelSerializer):
    fmea_item_function = serializers.CharField(
        source="fmea_item.function",
        read_only=True,
        default="",
    )
    grounded_warning = serializers.SerializerMethodField()

    class Meta:
        model = RCMItem
        fields = (
            "id",
            "analysis",
            "sequence",
            "function",
            "functional_failure",
            "failure_mode",
            "failure_effect",
            "safety_effect",
            "operational_effect",
            "detectability",
            "preventive_feasible",
            "suggested_strategy",
            "strategy",
            "is_overridden",
            "rationale",
            "fmea_item",
            "fmea_item_function",
            "grounded_warning",
            "is_demo",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "analysis",
            "suggested_strategy",
            "is_overridden",
            "is_demo",
        )
        extra_kwargs = {
            "sequence": {"required": False},
            "strategy": {"required": False},
            "fmea_item": {"required": False, "allow_null": True},
            "rationale": {"required": False, "allow_blank": True},
        }

    def get_grounded_warning(self, obj) -> bool:
        return RCMEvaluationService.grounded_warning(
            safety_effect=obj.safety_effect,
            preventive_feasible=obj.preventive_feasible,
        )


class RCMAnalysisSerializer(serializers.ModelSerializer):
    uav_class_code = serializers.CharField(source="uav_class.code", read_only=True)
    uav_class_name = serializers.CharField(source="uav_class.name", read_only=True)
    platform_code = serializers.CharField(source="platform_type.code", read_only=True)
    platform_name = serializers.CharField(source="platform_type.name", read_only=True)
    component_type_code = serializers.CharField(source="component_type.code", read_only=True)
    component_type_name = serializers.CharField(source="component_type.name", read_only=True)
    mission_code = serializers.CharField(source="mission_type.code", read_only=True, default="")
    mission_name = serializers.CharField(source="mission_type.name", read_only=True, default="")
    approved_by_name = serializers.CharField(
        source="approved_by.full_name",
        read_only=True,
        default="",
    )
    item_count = serializers.SerializerMethodField()
    items = RCMItemSerializer(many=True, read_only=True)

    class Meta:
        model = RCMAnalysis
        fields = (
            "id",
            "code",
            "title",
            "uav_class",
            "uav_class_code",
            "uav_class_name",
            "platform_type",
            "platform_code",
            "platform_name",
            "component_type",
            "component_type_code",
            "component_type_name",
            "mission_type",
            "mission_code",
            "mission_name",
            "status",
            "revision",
            "approved_at",
            "approved_by",
            "approved_by_name",
            "notes",
            "is_demo",
            "item_count",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("revision", "approved_at", "approved_by", "is_demo")
        extra_kwargs = {
            "mission_type": {"required": False, "allow_null": True},
        }

    def get_item_count(self, obj) -> int:
        annotated = getattr(obj, "item_count", None)
        if annotated is not None:
            return annotated
        if not obj.pk:
            return 0
        return obj.items.count()
