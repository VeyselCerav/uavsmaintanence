from __future__ import annotations

from django.db import IntegrityError
from django.db.models import Max, Q
from django.utils import timezone

from apps.core.api_exceptions import (
    FmeaAlreadyApproved,
    FmeaCodeTaken,
    FmeaLocked,
    InvalidFmeaScores,
)
from apps.core.models import SystemSetting
from apps.fmea.enums import FMEAStatus, RPNBand
from apps.fmea.models import FMEA, FMEAItem
from apps.maintenance.enums import DueStatus, Priority

DEFAULT_RPN_THRESHOLDS = {
    "low_max": 49,
    "medium_max": 99,
    "high_max": 199,
}

PRIORITY_RANK = {
    Priority.LOW: 1,
    Priority.MEDIUM: 2,
    Priority.HIGH: 3,
    Priority.CRITICAL: 4,
}
RANK_PRIORITY = {rank: code for code, rank in PRIORITY_RANK.items()}
EDITABLE_STATUSES = {FMEAStatus.DRAFT, FMEAStatus.IN_REVIEW}


class RPNService:
    KEY = "rpn.thresholds"

    @classmethod
    def thresholds(cls) -> dict[str, int]:
        setting = SystemSetting.objects.filter(key=cls.KEY).first()
        raw = setting.value if setting else DEFAULT_RPN_THRESHOLDS
        if not isinstance(raw, dict):
            raw = DEFAULT_RPN_THRESHOLDS
        return {
            "low_max": int(raw.get("low_max", DEFAULT_RPN_THRESHOLDS["low_max"])),
            "medium_max": int(raw.get("medium_max", DEFAULT_RPN_THRESHOLDS["medium_max"])),
            "high_max": int(raw.get("high_max", DEFAULT_RPN_THRESHOLDS["high_max"])),
        }

    @classmethod
    def compute(cls, severity: int, occurrence: int, detection: int) -> int:
        cls.validate_score(severity)
        cls.validate_score(occurrence)
        cls.validate_score(detection)
        return int(severity) * int(occurrence) * int(detection)

    @staticmethod
    def validate_score(value) -> None:
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise InvalidFmeaScores() from exc
        if number < 1 or number > 10:
            raise InvalidFmeaScores()

    @classmethod
    def band(cls, rpn: int | None) -> str | None:
        if rpn is None:
            return None
        thresholds = cls.thresholds()
        if rpn <= thresholds["low_max"]:
            return RPNBand.LOW
        if rpn <= thresholds["medium_max"]:
            return RPNBand.MEDIUM
        if rpn <= thresholds["high_max"]:
            return RPNBand.HIGH
        return RPNBand.CRITICAL


class FMEAService:
    @staticmethod
    def with_relations(fmea: FMEA) -> FMEA:
        return (
            FMEA.objects.select_related(
                "uav_class",
                "platform_type",
                "component_type",
                "mission_type",
                "approved_by",
            )
            .prefetch_related("items__catalog_mode")
            .get(pk=fmea.pk)
        )

    @staticmethod
    def ensure_editable(fmea: FMEA) -> None:
        if fmea.status not in EDITABLE_STATUSES:
            raise FmeaLocked()

    @classmethod
    def create(cls, *, actor, validated_data: dict) -> FMEA:
        code = validated_data["code"].strip()
        if FMEA.objects.filter(code=code).exists():
            raise FmeaCodeTaken()
        validated_data["code"] = code
        validated_data["title"] = validated_data["title"].strip()
        validated_data.setdefault("status", FMEAStatus.DRAFT)
        if validated_data.get("status") == FMEAStatus.APPROVED:
            validated_data["status"] = FMEAStatus.DRAFT
        fmea = FMEA(**validated_data)
        fmea.created_by = actor
        fmea.updated_by = actor
        try:
            fmea.save()
        except IntegrityError as exc:
            raise FmeaCodeTaken() from exc
        return cls.with_relations(fmea)

    @classmethod
    def update(cls, *, actor, fmea: FMEA, validated_data: dict) -> FMEA:
        status = validated_data.get("status", fmea.status)
        if fmea.status == FMEAStatus.APPROVED:
            if set(validated_data) - {"status", "notes"} and status != FMEAStatus.ARCHIVED:
                raise FmeaLocked()
            if status not in {FMEAStatus.APPROVED, FMEAStatus.ARCHIVED}:
                raise FmeaLocked()
        if "status" in validated_data and validated_data["status"] == FMEAStatus.APPROVED:
            raise FmeaLocked()
        if "code" in validated_data:
            code = validated_data["code"].strip()
            if FMEA.objects.filter(code=code).exclude(pk=fmea.pk).exists():
                raise FmeaCodeTaken()
            validated_data["code"] = code
        for field, value in validated_data.items():
            setattr(fmea, field, value)
        fmea.updated_by = actor
        try:
            fmea.save()
        except IntegrityError as exc:
            raise FmeaCodeTaken() from exc
        return cls.with_relations(fmea)

    @classmethod
    def approve(cls, *, actor, fmea: FMEA) -> FMEA:
        if fmea.status == FMEAStatus.APPROVED:
            raise FmeaAlreadyApproved()
        if fmea.status == FMEAStatus.ARCHIVED:
            raise FmeaLocked()
        fmea.status = FMEAStatus.APPROVED
        fmea.revision = (fmea.revision or 0) + 1
        fmea.approved_at = timezone.now()
        fmea.approved_by = actor
        fmea.updated_by = actor
        fmea.save(
            update_fields=[
                "status",
                "revision",
                "approved_at",
                "approved_by",
                "updated_by",
                "updated_at",
            ]
        )
        return cls.with_relations(fmea)


class FMEAItemService:
    @staticmethod
    def with_relations(item: FMEAItem) -> FMEAItem:
        return FMEAItem.objects.select_related("catalog_mode", "fmea").get(pk=item.pk)

    @classmethod
    def create(cls, *, actor, fmea: FMEA, validated_data: dict) -> FMEAItem:
        FMEAService.ensure_editable(fmea)
        current = (
            FMEAItem.objects.filter(fmea=fmea).aggregate(max_seq=Max("sequence")).get("max_seq")
        )
        validated_data.setdefault("sequence", (current or 0) + 1)
        validated_data["rpn"] = RPNService.compute(
            validated_data["severity"],
            validated_data["occurrence"],
            validated_data["detection"],
        )
        item = FMEAItem(fmea=fmea, **validated_data)
        item.created_by = actor
        item.updated_by = actor
        item.is_demo = fmea.is_demo
        item.save()
        return cls.with_relations(item)

    @classmethod
    def update(cls, *, actor, item: FMEAItem, validated_data: dict) -> FMEAItem:
        FMEAService.ensure_editable(item.fmea)
        for field, value in validated_data.items():
            setattr(item, field, value)
        item.rpn = RPNService.compute(item.severity, item.occurrence, item.detection)
        item.updated_by = actor
        item.save()
        return cls.with_relations(item)

    @classmethod
    def delete(cls, *, actor, item: FMEAItem) -> None:
        FMEAService.ensure_editable(item.fmea)
        item.updated_by = actor
        item.save(update_fields=["updated_by", "updated_at"])
        item.delete()


class MaintenancePriorityService:
    @staticmethod
    def at_least(current: str, minimum: str) -> str:
        return RANK_PRIORITY[max(PRIORITY_RANK[current], PRIORITY_RANK[minimum])]

    @classmethod
    def rpn_band_for(cls, *, uav, component) -> str | None:
        if uav is None or component is None:
            return None
        queryset = FMEA.objects.filter(
            status=FMEAStatus.APPROVED,
            uav_class_id=uav.uav_class_id,
            platform_type_id=uav.platform_type_id,
            component_type_id=component.component_type_id,
        ).filter(Q(mission_type_id=uav.mission_type_id) | Q(mission_type__isnull=True))
        analysis = (
            queryset.filter(mission_type_id=uav.mission_type_id).order_by("-revision").first()
        )
        if analysis is None:
            analysis = queryset.filter(mission_type__isnull=True).order_by("-revision").first()
        if analysis is None:
            return None
        max_rpn = analysis.items.aggregate(max_rpn=Max("rpn")).get("max_rpn")
        return RPNService.band(max_rpn)

    @classmethod
    def resolve(cls, *, base: str, due_status: str, rpn_band: str | None) -> str:
        result = base or Priority.MEDIUM
        if rpn_band == RPNBand.CRITICAL:
            result = cls.at_least(result, Priority.HIGH)
            if due_status == DueStatus.OVERDUE:
                result = Priority.CRITICAL
        if rpn_band == RPNBand.HIGH and due_status in {DueStatus.DUE, DueStatus.OVERDUE}:
            result = cls.at_least(result, Priority.HIGH)
        if due_status == DueStatus.CRITICAL:
            result = Priority.CRITICAL
        if due_status == DueStatus.OVERDUE and PRIORITY_RANK[result] < PRIORITY_RANK[Priority.HIGH]:
            result = Priority.HIGH
        return result

    @classmethod
    def resolve_for_due(cls, due) -> str:
        band = cls.rpn_band_for(uav=due.uav, component=due.component)
        base = due.template_item.priority if due.template_item_id else due.priority
        return cls.resolve(base=base, due_status=due.status, rpn_band=band)
