from __future__ import annotations

from django.db import IntegrityError
from django.db.models import Max
from django.utils import timezone

from apps.core.api_exceptions import (
    RcmAlreadyApproved,
    RcmCodeTaken,
    RcmLocked,
    RcmNotApproved,
    RcmRationaleRequired,
    RcmStrategyConflict,
)
from apps.maintenance.enums import RCMStrategy
from apps.maintenance.models import MaintenanceTemplate, MaintenanceTemplateItem
from apps.rcm.enums import Detectability, RCMStatus
from apps.rcm.models import RCMAnalysis, RCMItem

EDITABLE_STATUSES = {RCMStatus.DRAFT, RCMStatus.IN_REVIEW}


class RCMEvaluationService:
    @classmethod
    def evaluate(
        cls,
        *,
        safety_effect: bool,
        operational_effect: bool,
        preventive_feasible: bool,
        detectability: str,
    ) -> str:
        if safety_effect:
            if preventive_feasible:
                if detectability == Detectability.HIGH:
                    return RCMStrategy.CONDITION_INSPECTION
                return RCMStrategy.SCHEDULED_RESTORATION
            return RCMStrategy.CORRECTIVE
        if operational_effect:
            if preventive_feasible:
                if detectability == Detectability.HIGH:
                    return RCMStrategy.CONDITION_INSPECTION
                return RCMStrategy.SCHEDULED_INSPECTION
            return RCMStrategy.CORRECTIVE
        if preventive_feasible:
            return RCMStrategy.FUNCTIONAL_CHECK
        return RCMStrategy.CORRECTIVE

    @staticmethod
    def grounded_warning(*, safety_effect: bool, preventive_feasible: bool) -> bool:
        return bool(safety_effect) and not bool(preventive_feasible)

    @classmethod
    def resolve_strategy(cls, data: dict, *, existing: RCMItem | None = None) -> dict:
        safety = data.get(
            "safety_effect",
            existing.safety_effect if existing else False,
        )
        operational = data.get(
            "operational_effect",
            existing.operational_effect if existing else False,
        )
        preventive = data.get(
            "preventive_feasible",
            existing.preventive_feasible if existing else True,
        )
        detectability = data.get(
            "detectability",
            existing.detectability if existing else Detectability.MEDIUM,
        )
        suggested = cls.evaluate(
            safety_effect=bool(safety),
            operational_effect=bool(operational),
            preventive_feasible=bool(preventive),
            detectability=detectability,
        )
        strategy = data.get("strategy") or (existing.strategy if existing else None) or suggested
        rationale = (data.get("rationale") if "rationale" in data else None)
        if rationale is None:
            rationale = existing.rationale if existing else ""
        rationale = (rationale or "").strip()
        overridden = strategy != suggested
        if overridden and not rationale:
            raise RcmRationaleRequired()
        data["suggested_strategy"] = suggested
        data["strategy"] = strategy
        data["is_overridden"] = overridden
        if "rationale" in data or overridden:
            data["rationale"] = rationale
        return data


class RCMService:
    @staticmethod
    def with_relations(analysis: RCMAnalysis) -> RCMAnalysis:
        return (
            RCMAnalysis.objects.select_related(
                "uav_class",
                "platform_type",
                "component_type",
                "mission_type",
                "approved_by",
            )
            .prefetch_related("items__fmea_item")
            .get(pk=analysis.pk)
        )

    @staticmethod
    def ensure_editable(analysis: RCMAnalysis) -> None:
        if analysis.status not in EDITABLE_STATUSES:
            raise RcmLocked()

    @classmethod
    def create(cls, *, actor, validated_data: dict) -> RCMAnalysis:
        code = validated_data["code"].strip()
        if RCMAnalysis.objects.filter(code=code).exists():
            raise RcmCodeTaken()
        validated_data["code"] = code
        validated_data["title"] = validated_data["title"].strip()
        validated_data.setdefault("status", RCMStatus.DRAFT)
        if validated_data.get("status") == RCMStatus.APPROVED:
            validated_data["status"] = RCMStatus.DRAFT
        analysis = RCMAnalysis(**validated_data)
        analysis.created_by = actor
        analysis.updated_by = actor
        try:
            analysis.save()
        except IntegrityError as exc:
            raise RcmCodeTaken() from exc
        return cls.with_relations(analysis)

    @classmethod
    def update(cls, *, actor, analysis: RCMAnalysis, validated_data: dict) -> RCMAnalysis:
        status = validated_data.get("status", analysis.status)
        if analysis.status == RCMStatus.APPROVED:
            extra = set(validated_data) - {"status", "notes"}
            if extra and status != RCMStatus.ARCHIVED:
                raise RcmLocked()
            if status not in {RCMStatus.APPROVED, RCMStatus.ARCHIVED}:
                raise RcmLocked()
        if "status" in validated_data and validated_data["status"] == RCMStatus.APPROVED:
            raise RcmLocked()
        if "code" in validated_data:
            code = validated_data["code"].strip()
            if RCMAnalysis.objects.filter(code=code).exclude(pk=analysis.pk).exists():
                raise RcmCodeTaken()
            validated_data["code"] = code
        for field, value in validated_data.items():
            setattr(analysis, field, value)
        analysis.updated_by = actor
        try:
            analysis.save()
        except IntegrityError as exc:
            raise RcmCodeTaken() from exc
        return cls.with_relations(analysis)

    @classmethod
    def approve(cls, *, actor, analysis: RCMAnalysis) -> RCMAnalysis:
        if analysis.status == RCMStatus.APPROVED:
            raise RcmAlreadyApproved()
        if analysis.status == RCMStatus.ARCHIVED:
            raise RcmLocked()
        for item in analysis.items.all():
            if item.is_overridden and not (item.rationale or "").strip():
                raise RcmRationaleRequired()
        analysis.status = RCMStatus.APPROVED
        analysis.revision = (analysis.revision or 0) + 1
        analysis.approved_at = timezone.now()
        analysis.approved_by = actor
        analysis.updated_by = actor
        analysis.save(
            update_fields=[
                "status",
                "revision",
                "approved_at",
                "approved_by",
                "updated_by",
                "updated_at",
            ]
        )
        return cls.with_relations(analysis)

    @classmethod
    def evaluate(cls, *, actor, analysis: RCMAnalysis) -> RCMAnalysis:
        cls.ensure_editable(analysis)
        for item in analysis.items.all():
            payload = RCMEvaluationService.resolve_strategy(
                {
                    "safety_effect": item.safety_effect,
                    "operational_effect": item.operational_effect,
                    "preventive_feasible": item.preventive_feasible,
                    "detectability": item.detectability,
                    "strategy": None if not item.is_overridden else item.strategy,
                    "rationale": item.rationale,
                },
                existing=item,
            )
            item.suggested_strategy = payload["suggested_strategy"]
            item.strategy = payload["strategy"]
            item.is_overridden = payload["is_overridden"]
            item.updated_by = actor
            item.save(
                update_fields=[
                    "suggested_strategy",
                    "strategy",
                    "is_overridden",
                    "updated_by",
                    "updated_at",
                ]
            )
        return cls.with_relations(analysis)

    @classmethod
    def apply_to_template(cls, *, actor, analysis: RCMAnalysis) -> dict:
        if analysis.status != RCMStatus.APPROVED:
            raise RcmNotApproved()
        items = list(analysis.items.all())
        strategies = {item.strategy for item in items}
        if len(strategies) != 1:
            raise RcmStrategyConflict()
        strategy = strategies.pop()
        templates = MaintenanceTemplate.objects.filter(
            uav_class_id=analysis.uav_class_id,
            platform_type_id=analysis.platform_type_id,
        )
        if analysis.mission_type_id:
            templates = templates.filter(mission_type_id=analysis.mission_type_id)
        updated = MaintenanceTemplateItem.objects.filter(
            template__in=templates,
            component_type_id=analysis.component_type_id,
        ).update(rcm_strategy=strategy, updated_by=actor)
        return {"updated": updated, "strategy": strategy}


class RCMItemService:
    @staticmethod
    def with_relations(item: RCMItem) -> RCMItem:
        return RCMItem.objects.select_related("fmea_item", "analysis").get(pk=item.pk)

    @classmethod
    def create(cls, *, actor, analysis: RCMAnalysis, validated_data: dict) -> RCMItem:
        RCMService.ensure_editable(analysis)
        current = (
            RCMItem.objects.filter(analysis=analysis)
            .aggregate(max_seq=Max("sequence"))
            .get("max_seq")
        )
        validated_data.setdefault("sequence", (current or 0) + 1)
        validated_data = RCMEvaluationService.resolve_strategy(validated_data)
        item = RCMItem(analysis=analysis, **validated_data)
        item.created_by = actor
        item.updated_by = actor
        item.is_demo = analysis.is_demo
        item.save()
        return cls.with_relations(item)

    @classmethod
    def update(cls, *, actor, item: RCMItem, validated_data: dict) -> RCMItem:
        RCMService.ensure_editable(item.analysis)
        validated_data = RCMEvaluationService.resolve_strategy(validated_data, existing=item)
        for field, value in validated_data.items():
            setattr(item, field, value)
        item.updated_by = actor
        item.save()
        return cls.with_relations(item)

    @classmethod
    def delete(cls, *, actor, item: RCMItem) -> None:
        RCMService.ensure_editable(item.analysis)
        item.updated_by = actor
        item.save(update_fields=["updated_by", "updated_at"])
        item.delete()
