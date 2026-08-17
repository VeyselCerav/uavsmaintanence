from django.db import models
from django.db.models import Q

from apps.core.models import SoftDeleteModel
from apps.flights.enums import FlightResult


class Flight(SoftDeleteModel):
    flight_number = models.CharField(max_length=64)
    uav = models.ForeignKey("uavs.UAV", on_delete=models.PROTECT, related_name="flights")
    operator = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="operated_flights",
    )
    mission_type = models.ForeignKey(
        "uavs.MissionType",
        on_delete=models.PROTECT,
        related_name="flights",
    )
    flown_on = models.DateField()
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    duration_hours = models.DecimalField(max_digits=12, decimal_places=2)
    distance_km = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_altitude_m = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_speed_kmh = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    weather = models.CharField(max_length=255, blank=True)
    result = models.CharField(
        max_length=32,
        choices=FlightResult.choices,
        default=FlightResult.COMPLETED,
    )
    notes = models.TextField(blank=True)
    counters_applied = models.BooleanField(default=False)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "flight"
        indexes = [
            models.Index(fields=["uav", "-start_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["flight_number"],
                condition=Q(is_deleted=False),
                name="uniq_flight_number_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.flight_number
