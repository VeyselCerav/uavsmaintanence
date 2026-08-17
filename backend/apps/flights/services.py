from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import F, Max
from django.utils import timezone

from apps.components.enums import ComponentStatus
from apps.components.models import UAVComponent
from apps.core.api_exceptions import FlightCountersAlreadyApplied, InvalidFlightInterval
from apps.flights.enums import FlightResult
from apps.flights.models import Flight
from apps.maintenance.services import MaintenanceDueService
from apps.uavs.models import UAV


class FlightService:
    @staticmethod
    def with_relations(flight: Flight) -> Flight:
        return Flight.objects.select_related("uav", "operator", "mission_type").get(pk=flight.pk)

    @staticmethod
    def next_number() -> str:
        year = timezone.now().year
        prefix = f"FL-{year}-"
        last = (
            Flight.objects.filter(flight_number__startswith=prefix)
            .aggregate(max_number=Max("flight_number"))
            .get("max_number")
        )
        sequence = 1
        if last:
            sequence = int(str(last).rsplit("-", maxsplit=1)[-1]) + 1
        return f"{prefix}{sequence:06d}"

    @staticmethod
    def resolve_duration(start_at, end_at, duration_hours) -> Decimal:
        if end_at <= start_at:
            raise InvalidFlightInterval()
        if duration_hours:
            value = Decimal(str(duration_hours))
        else:
            seconds = Decimal(str((end_at - start_at).total_seconds()))
            value = (seconds / Decimal("3600")).quantize(Decimal("0.01"))
        if value <= 0:
            raise InvalidFlightInterval()
        return value

    @classmethod
    def create(cls, *, actor, validated_data: dict) -> Flight:
        role = getattr(getattr(actor, "role", None), "code", "")
        if role == "OPERATOR" or validated_data.get("operator") is None:
            validated_data["operator"] = actor
        if not validated_data.get("flight_number"):
            validated_data["flight_number"] = cls.next_number()
        validated_data["duration_hours"] = cls.resolve_duration(
            validated_data["start_at"],
            validated_data["end_at"],
            validated_data.get("duration_hours"),
        )
        if not validated_data.get("flown_on"):
            start_at = validated_data["start_at"]
            if timezone.is_aware(start_at):
                validated_data["flown_on"] = timezone.localtime(start_at).date()
            else:
                validated_data["flown_on"] = start_at.date()
        if not validated_data.get("mission_type"):
            validated_data["mission_type"] = validated_data["uav"].mission_type
        flight = Flight(**validated_data)
        flight.created_by = actor
        flight.updated_by = actor
        flight.save()
        return flight

    @classmethod
    def update(cls, *, actor, flight: Flight, validated_data: dict) -> Flight:
        if flight.counters_applied:
            raise FlightCountersAlreadyApplied()
        for field, value in validated_data.items():
            setattr(flight, field, value)
        flight.duration_hours = cls.resolve_duration(
            flight.start_at,
            flight.end_at,
            flight.duration_hours,
        )
        flight.updated_by = actor
        flight.save()
        return flight

    @classmethod
    def complete(cls, *, actor, flight: Flight) -> Flight:
        with transaction.atomic():
            locked = Flight.objects.select_for_update().get(pk=flight.pk)
            if locked.counters_applied:
                raise FlightCountersAlreadyApplied()
            uav = UAV.objects.select_for_update().get(pk=locked.uav_id)
            duration = locked.duration_hours
            uav.total_flight_hours = F("total_flight_hours") + duration
            uav.total_flight_count = F("total_flight_count") + 1
            uav.total_flight_cycles = F("total_flight_cycles") + 1
            uav.save(
                update_fields=["total_flight_hours", "total_flight_count", "total_flight_cycles"]
            )
            UAVComponent.objects.filter(uav=uav, status=ComponentStatus.INSTALLED).update(
                operating_hours=F("operating_hours") + duration,
                cycle_count=F("cycle_count") + 1,
            )
            locked.result = FlightResult.COMPLETED
            locked.counters_applied = True
            locked.updated_by = actor
            locked.save(update_fields=["result", "counters_applied", "updated_by", "updated_at"])
            uav.refresh_from_db()
            MaintenanceDueService.recalculate(uav)
        return cls.with_relations(locked)
