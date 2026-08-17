from rest_framework import serializers

from apps.flights.models import Flight


class FlightSerializer(serializers.ModelSerializer):
    uav_registration = serializers.CharField(source="uav.registration_number", read_only=True)
    operator_name = serializers.CharField(source="operator.full_name", read_only=True, default="")
    mission_name = serializers.CharField(source="mission_type.name", read_only=True)
    mission_code = serializers.CharField(source="mission_type.code", read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "flight_number",
            "uav",
            "uav_registration",
            "operator",
            "operator_name",
            "mission_type",
            "mission_code",
            "mission_name",
            "flown_on",
            "start_at",
            "end_at",
            "duration_hours",
            "distance_km",
            "max_altitude_m",
            "max_speed_kmh",
            "weather",
            "result",
            "notes",
            "counters_applied",
            "is_demo",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("counters_applied",)
        extra_kwargs = {
            "flight_number": {"required": False, "allow_blank": True},
            "mission_type": {"required": False, "allow_null": True},
            "operator": {"required": False, "allow_null": True},
            "flown_on": {"required": False},
            "duration_hours": {"required": False, "allow_null": True},
        }
