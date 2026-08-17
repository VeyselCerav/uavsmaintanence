from django.db.models import Max
from rest_framework import serializers

from apps.fmea.models import FMEA, FMEAItem
from apps.fmea.services import RPNService


class FMEAItemSerializer(serializers.ModelSerializer):
    catalog_mode_code = serializers.CharField(
        source="catalog_mode.code",
        read_only=True,
        default="",
    )
    catalog_mode_name = serializers.CharField(
        source="catalog_mode.name",
        read_only=True,
        default="",
    )
    rpn_band = serializers.SerializerMethodField()

    class Meta:
        model = FMEAItem
        fields = (
            "id",
            "fmea",
            "sequence",
            "function",
            "functional_failure",
            "failure_mode",
            "catalog_mode",
            "catalog_mode_code",
            "catalog_mode_name",
            "failure_cause",
            "failure_effect",
            "severity",
            "occurrence",
            "detection",
            "rpn",
            "rpn_band",
            "existing_control",
            "recommended_action",
            "is_demo",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("fmea", "rpn", "is_demo")
        extra_kwargs = {
            "catalog_mode": {"required": False, "allow_null": True},
            "sequence": {"required": False},
        }

    def get_rpn_band(self, obj) -> str | None:
        return RPNService.band(obj.rpn)


class FMEASerializer(serializers.ModelSerializer):
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
    max_rpn = serializers.SerializerMethodField()
    rpn_band = serializers.SerializerMethodField()
    items = FMEAItemSerializer(many=True, read_only=True)

    class Meta:
        model = FMEA
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
            "max_rpn",
            "rpn_band",
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

    def get_max_rpn(self, obj) -> int | None:
        annotated = getattr(obj, "max_rpn", None)
        if annotated is not None:
            return annotated
        if not obj.pk:
            return None
        return obj.items.aggregate(max_rpn=Max("rpn")).get("max_rpn")

    def get_rpn_band(self, obj) -> str | None:
        return RPNService.band(self.get_max_rpn(obj))
