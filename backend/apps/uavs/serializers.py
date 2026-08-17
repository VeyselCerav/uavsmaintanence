from rest_framework import serializers

from apps.uavs.models import UAV, MissionType, PlatformType, UAVClass


class CatalogSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "id",
            "code",
            "name",
            "description",
            "is_active",
            "is_demo",
            "created_at",
            "updated_at",
        )


class UAVClassSerializer(CatalogSerializer):
    class Meta(CatalogSerializer.Meta):
        model = UAVClass
        fields = CatalogSerializer.Meta.fields + ("mtow_min_kg", "mtow_max_kg", "sort_order")


class PlatformTypeSerializer(CatalogSerializer):
    class Meta(CatalogSerializer.Meta):
        model = PlatformType


class MissionTypeSerializer(CatalogSerializer):
    class Meta(CatalogSerializer.Meta):
        model = MissionType


class UAVSerializer(serializers.ModelSerializer):
    uav_class_code = serializers.CharField(source="uav_class.code", read_only=True)
    uav_class_name = serializers.CharField(source="uav_class.name", read_only=True)
    platform_code = serializers.CharField(source="platform_type.code", read_only=True)
    platform_name = serializers.CharField(source="platform_type.name", read_only=True)
    mission_code = serializers.CharField(source="mission_type.code", read_only=True)
    mission_name = serializers.CharField(source="mission_type.name", read_only=True)
    template_code = serializers.CharField(source="maintenance_template.code", read_only=True)
    template_name = serializers.CharField(source="maintenance_template.name", read_only=True)

    class Meta:
        model = UAV
        fields = (
            "id",
            "registration_number",
            "serial_number",
            "manufacturer",
            "model",
            "uav_class",
            "uav_class_code",
            "uav_class_name",
            "platform_type",
            "platform_code",
            "platform_name",
            "mission_type",
            "mission_code",
            "mission_name",
            "maintenance_template",
            "template_code",
            "template_name",
            "maintenance_approach",
            "mtow_kg",
            "production_date",
            "inventory_entry_date",
            "total_flight_hours",
            "total_flight_count",
            "total_flight_cycles",
            "status",
            "notes",
            "is_demo",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "maintenance_template",
            "template_code",
            "template_name",
            "total_flight_hours",
            "total_flight_count",
            "total_flight_cycles",
        )
