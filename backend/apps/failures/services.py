from __future__ import annotations

from decimal import Decimal

from django.db import IntegrityError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.core.api_exceptions import (
    FailureModeCodeTaken,
    InvalidFailureComponent,
    InvalidFailureDates,
    InvalidFailureDowntime,
    InvalidFailureWorkOrder,
)
from apps.failures.models import Failure, FailureMode


class FailureModeService:
    @classmethod
    def create(cls, *, actor, data: dict) -> FailureMode:
        code = data["code"].strip()
        if FailureMode.objects.filter(code=code).exists():
            raise FailureModeCodeTaken()
        mode = FailureMode(
            code=code,
            name=data["name"].strip(),
            description=data.get("description") or "",
            is_active=data.get("is_active", True),
            is_demo=bool(data.get("is_demo", False)),
            created_by=actor,
            updated_by=actor,
        )
        try:
            mode.save()
        except IntegrityError as exc:
            raise FailureModeCodeTaken() from exc
        return mode

    @classmethod
    def update(cls, *, actor, mode: FailureMode, data: dict) -> FailureMode:
        if "code" in data:
            code = data["code"].strip()
            if FailureMode.objects.filter(code=code).exclude(pk=mode.pk).exists():
                raise FailureModeCodeTaken()
            mode.code = code
        if "name" in data:
            mode.name = data["name"].strip()
        if "description" in data:
            mode.description = data["description"]
        if "is_active" in data:
            mode.is_active = data["is_active"]
        mode.updated_by = actor
        try:
            mode.save()
        except IntegrityError as exc:
            raise FailureModeCodeTaken() from exc
        return mode


class FailureService:
    @staticmethod
    def with_relations(failure: Failure) -> Failure:
        return Failure.objects.select_related(
            "uav",
            "component",
            "failure_mode",
            "work_order",
        ).get(pk=failure.pk)

    @staticmethod
    def validate(data: dict) -> None:
        occurred_at = data.get("occurred_at")
        resolved_at = data.get("resolved_at")
        if occurred_at and resolved_at and resolved_at < occurred_at:
            raise InvalidFailureDates()
        downtime = data.get("downtime_hours")
        if downtime is not None and Decimal(str(downtime)) < 0:
            raise InvalidFailureDowntime()
        uav = data.get("uav")
        component = data.get("component")
        if uav is not None and component is not None and component.uav_id != uav.id:
            raise InvalidFailureComponent()
        work_order = data.get("work_order")
        if uav is not None and work_order is not None and work_order.uav_id != uav.id:
            raise InvalidFailureWorkOrder()

    @classmethod
    def create(cls, *, actor, validated_data: dict) -> Failure:
        if not validated_data.get("occurred_at"):
            validated_data["occurred_at"] = timezone.now()
        if validated_data.get("downtime_hours") is None:
            validated_data["downtime_hours"] = Decimal("0")
        cls.validate(validated_data)
        failure = Failure(**validated_data)
        failure.created_by = actor
        failure.updated_by = actor
        failure.save()
        return cls.with_relations(failure)

    @classmethod
    def update(cls, *, actor, failure: Failure, validated_data: dict) -> Failure:
        for field, value in validated_data.items():
            setattr(failure, field, value)
        cls.validate(
            {
                "occurred_at": failure.occurred_at,
                "resolved_at": failure.resolved_at,
                "downtime_hours": failure.downtime_hours,
                "uav": failure.uav,
                "component": failure.component,
                "work_order": failure.work_order,
            }
        )
        failure.updated_by = actor
        failure.save()
        return cls.with_relations(failure)

    @classmethod
    def resolve(cls, *, actor, failure: Failure, resolved_at=None) -> Failure:
        when = resolved_at or timezone.now()
        if isinstance(when, str):
            parsed = parse_datetime(when)
            if parsed is None:
                raise InvalidFailureDates()
            when = parsed
        return cls.update(actor=actor, failure=failure, validated_data={"resolved_at": when})
