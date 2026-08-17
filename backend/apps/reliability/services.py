from __future__ import annotations

from datetime import datetime, time
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from apps.components.models import UAVComponent
from apps.core.api_exceptions import (
    InvalidReliabilityRange,
    InvalidReliabilityScope,
    ReliabilityScopeNotFound,
)
from apps.core.models import SystemSetting
from apps.failures.models import Failure
from apps.flights.enums import FlightResult
from apps.flights.models import Flight
from apps.reliability.enums import ReliabilityScope, ZeroFailurePolicy
from apps.uavs.models import UAV, UAVClass

HOURS = Decimal("0.01")
RATIO = Decimal("0.0001")
SETTING_KEY = "reliability.zero_failure_policy"


def _quantize(value: Decimal | None, places: Decimal) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(places, rounding=ROUND_HALF_UP)


def _as_str(value: Decimal | None, places: Decimal) -> str | None:
    quantized = _quantize(value, places)
    if quantized is None:
        return None
    return format(quantized, "f")


def _parse_bound(value: str | None, *, end: bool) -> datetime | None:
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        parsed_date = parse_date(value)
        if parsed_date is None:
            raise InvalidReliabilityRange()
        clock = time.max if end else time.min
        parsed = datetime.combine(parsed_date, clock)
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


class ReliabilityService:
    @classmethod
    def policy(cls) -> str:
        setting = SystemSetting.objects.filter(key=SETTING_KEY).first()
        raw = setting.value if setting else ZeroFailurePolicy.UNDEFINED
        if isinstance(raw, dict):
            raw = raw.get("policy", ZeroFailurePolicy.UNDEFINED)
        if raw not in ZeroFailurePolicy.values:
            return ZeroFailurePolicy.UNDEFINED
        return raw

    @classmethod
    def compute(
        cls,
        *,
        scope: str,
        scope_id: str | None = None,
        period_start: str | None = None,
        period_end: str | None = None,
    ) -> dict:
        if scope not in ReliabilityScope.values:
            raise InvalidReliabilityScope()
        start = _parse_bound(period_start, end=False)
        end = _parse_bound(period_end, end=True)
        if start and end and start > end:
            raise InvalidReliabilityRange()
        uavs, component, label = cls._resolve_scope(scope=scope, scope_id=scope_id)
        metrics = cls.metrics_for_uavs(uavs, component=component, start=start, end=end)
        return {
            "scope": scope,
            "scope_id": str(scope_id) if scope_id else None,
            "scope_label": label,
            "period_start": start.isoformat() if start else None,
            "period_end": end.isoformat() if end else None,
            **metrics,
        }

    @classmethod
    def metrics_for_uavs(cls, uavs, *, component=None, start=None, end=None) -> dict:
        uav_ids = list(uavs.values_list("id", flat=True))
        operating = cls._operating_hours(
            uavs=uavs,
            component=component,
            start=start,
            end=end,
        )
        failures = Failure.objects.filter(uav_id__in=uav_ids)
        if component is not None:
            failures = failures.filter(component_id=component.id)
        if start:
            failures = failures.filter(occurred_at__gte=start)
        if end:
            failures = failures.filter(occurred_at__lte=end)
        failure_count = failures.count()
        repairs = failures.filter(resolved_at__isnull=False)
        repair_count = repairs.count()
        total_repair = repairs.aggregate(total=Sum("downtime_hours")).get("total") or Decimal("0")
        policy = cls.policy()
        is_lower_bound = False
        mtbf = None
        if failure_count > 0:
            mtbf = operating / Decimal(failure_count)
        elif policy == ZeroFailurePolicy.OPERATING_TIME_AS_LOWER_BOUND:
            mtbf = operating
            is_lower_bound = True
        mttr = None
        if repair_count > 0:
            mttr = total_repair / Decimal(repair_count)
        availability = None
        if mtbf is not None and mttr is not None:
            denominator = mtbf + mttr
            if denominator > 0:
                availability = mtbf / denominator
        return {
            "operating_hours": _as_str(operating, HOURS),
            "failure_count": failure_count,
            "repair_count": repair_count,
            "total_repair_hours": _as_str(total_repair, HOURS),
            "mtbf_hours": _as_str(mtbf, HOURS),
            "mttr_hours": _as_str(mttr, HOURS),
            "availability": _as_str(availability, RATIO),
            "zero_failure_policy": policy,
            "is_lower_bound": is_lower_bound,
        }

    @classmethod
    def _resolve_scope(cls, *, scope: str, scope_id: str | None):
        if scope == ReliabilityScope.FLEET:
            uavs = UAV.objects.all()
            return uavs, None, "fleet"
        if not scope_id:
            raise InvalidReliabilityScope()
        if scope == ReliabilityScope.CLASS:
            uav_class = UAVClass.objects.filter(pk=scope_id).first()
            if uav_class is None:
                raise ReliabilityScopeNotFound()
            return UAV.objects.filter(uav_class=uav_class), None, uav_class.code
        if scope == ReliabilityScope.UAV:
            uav = UAV.objects.filter(pk=scope_id).first()
            if uav is None:
                raise ReliabilityScopeNotFound()
            return UAV.objects.filter(pk=uav.pk), None, uav.registration_number
        component = UAVComponent.objects.select_related(
            "uav",
            "component_type",
        ).filter(pk=scope_id).first()
        if component is None:
            raise ReliabilityScopeNotFound()
        return (
            UAV.objects.filter(pk=component.uav_id),
            component,
            component.name,
        )

    @classmethod
    def _operating_hours(cls, *, uavs, component, start, end) -> Decimal:
        if start or end:
            flights = Flight.objects.filter(
                uav_id__in=uavs.values("id"),
                result=FlightResult.COMPLETED,
            )
            if start:
                flights = flights.filter(start_at__gte=start)
            if end:
                flights = flights.filter(start_at__lte=end)
            total = flights.aggregate(total=Sum("duration_hours")).get("total")
            return total or Decimal("0")
        if component is not None:
            return component.operating_hours or Decimal("0")
        total = uavs.aggregate(total=Sum("total_flight_hours")).get("total")
        return total or Decimal("0")
