from rest_framework import serializers

from apps.components.enums import ComponentStatus
from apps.components.models import ComponentType, UAVComponent
from apps.uavs.models import UAV


class ComponentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComponentType
        fields = (
            "id",
            "code",
            "name",
            "description",
            "tracks_hours",
            "tracks_cycles",
            "is_active",
            "is_demo",
            "created_at",
            "updated_at",
        )


class UAVComponentSerializer(serializers.ModelSerializer):
    uav_registration = serializers.CharField(source="uav.registration_number", read_only=True)
    component_type_code = serializers.CharField(source="component_type.code", read_only=True)
    component_type_name = serializers.CharField(source="component_type.name", read_only=True)

    class Meta:
        model = UAVComponent
        fields = (
            "id",
            "uav",
            "uav_registration",
            "component_type",
            "component_type_code",
            "component_type_name",
            "name",
            "serial_number",
            "part_number",
            "manufacturer",
            "model",
            "installed_at",
            "removed_at",
            "operating_hours",
            "cycle_count",
            "status",
            "notes",
            "is_demo",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class UAVComponentInstallSerializer(serializers.Serializer):
    uav = serializers.PrimaryKeyRelatedField(queryset=UAV.objects.all())
    component_type = serializers.PrimaryKeyRelatedField(queryset=ComponentType.objects.all())
    name = serializers.CharField(max_length=128, required=False, allow_blank=True)
    serial_number = serializers.CharField(max_length=128, required=False, allow_blank=True)
    part_number = serializers.CharField(max_length=128, required=False, allow_blank=True)
    manufacturer = serializers.CharField(max_length=128, required=False, allow_blank=True)
    model = serializers.CharField(max_length=128, required=False, allow_blank=True)
    installed_at = serializers.DateTimeField(required=False)
    operating_hours = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, min_value=0
    )
    cycle_count = serializers.IntegerField(required=False, min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True)


class UAVComponentUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128, required=False)
    part_number = serializers.CharField(max_length=128, required=False, allow_blank=True)
    manufacturer = serializers.CharField(max_length=128, required=False, allow_blank=True)
    model = serializers.CharField(max_length=128, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class UAVComponentRemoveSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            ComponentStatus.REMOVED,
            ComponentStatus.QUARANTINE,
            ComponentStatus.SCRAPPED,
        ],
        required=False,
        default=ComponentStatus.REMOVED,
    )
    removed_at = serializers.DateTimeField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
