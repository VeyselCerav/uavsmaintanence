from rest_framework import serializers

from apps.failures.models import Failure, FailureMode


class FailureModeSerializer(serializers.ModelSerializer):
    code = serializers.CharField(max_length=64)

    class Meta:
        model = FailureMode
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
        read_only_fields = ("is_demo",)
        validators = []


class FailureSerializer(serializers.ModelSerializer):
    uav_registration = serializers.CharField(source="uav.registration_number", read_only=True)
    component_name = serializers.CharField(
        source="component.name",
        read_only=True,
        default="",
    )
    failure_mode_code = serializers.CharField(
        source="failure_mode.code",
        read_only=True,
        default="",
    )
    failure_mode_name = serializers.CharField(
        source="failure_mode.name",
        read_only=True,
        default="",
    )
    work_order_number = serializers.CharField(
        source="work_order.number",
        read_only=True,
        default="",
    )

    class Meta:
        model = Failure
        fields = (
            "id",
            "uav",
            "uav_registration",
            "component",
            "component_name",
            "failure_mode",
            "failure_mode_code",
            "failure_mode_name",
            "occurred_at",
            "discovered_during",
            "severity",
            "description",
            "downtime_hours",
            "resolved_at",
            "work_order",
            "work_order_number",
            "is_demo",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "occurred_at": {"required": False},
            "component": {"required": False, "allow_null": True},
            "failure_mode": {"required": False, "allow_null": True},
            "work_order": {"required": False, "allow_null": True},
            "resolved_at": {"required": False, "allow_null": True},
            "downtime_hours": {"required": False},
        }
