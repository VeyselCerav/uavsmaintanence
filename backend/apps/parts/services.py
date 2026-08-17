from __future__ import annotations

from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.api_exceptions import (
    InsufficientStock,
    InvalidCostAmount,
    InvalidPartQuantity,
    PartIncompatible,
    PartNumberTaken,
)
from apps.maintenance.models import WorkOrder
from apps.parts.enums import Currency
from apps.parts.models import CostRecord, Part, PartCompatibility, WorkOrderPart


def _money(value) -> Decimal:
    amount = Decimal(str(value or 0))
    if amount < 0:
        raise InvalidCostAmount()
    return amount


class PartService:
    @staticmethod
    def with_relations(part: Part) -> Part:
        return Part.objects.prefetch_related(
            "compatibilities__uav_class",
            "compatibilities__platform_type",
            "compatibilities__component_type",
        ).get(pk=part.pk)

    @classmethod
    def create(cls, *, actor, validated_data: dict) -> Part:
        number = validated_data["part_number"].strip()
        if Part.objects.filter(part_number=number).exists():
            raise PartNumberTaken()
        validated_data["part_number"] = number
        validated_data["name"] = validated_data["name"].strip()
        part = Part(**validated_data)
        part.created_by = actor
        part.updated_by = actor
        try:
            part.save()
        except IntegrityError as exc:
            raise PartNumberTaken() from exc
        return cls.with_relations(part)

    @classmethod
    def update(cls, *, actor, part: Part, validated_data: dict) -> Part:
        if "part_number" in validated_data:
            number = validated_data["part_number"].strip()
            if Part.objects.filter(part_number=number).exclude(pk=part.pk).exists():
                raise PartNumberTaken()
            validated_data["part_number"] = number
        for field, value in validated_data.items():
            setattr(part, field, value)
        part.updated_by = actor
        try:
            part.save()
        except IntegrityError as exc:
            raise PartNumberTaken() from exc
        return cls.with_relations(part)


class PartCompatibilityService:
    @classmethod
    def create(cls, *, actor, part: Part, validated_data: dict) -> PartCompatibility:
        row = PartCompatibility(part=part, **validated_data)
        row.created_by = actor
        row.updated_by = actor
        row.is_demo = part.is_demo
        row.save()
        return row

    @classmethod
    def delete(cls, *, actor, row: PartCompatibility) -> None:
        row.updated_by = actor
        row.save(update_fields=["updated_by", "updated_at"])
        row.delete()


class CostRecordService:
    @staticmethod
    def total(part_cost, labor_cost, other_cost) -> Decimal:
        return _money(part_cost) + _money(labor_cost) + _money(other_cost)

    @classmethod
    def create(cls, *, actor, validated_data: dict) -> CostRecord:
        validated_data["part_cost"] = _money(validated_data.get("part_cost"))
        validated_data["labor_cost"] = _money(validated_data.get("labor_cost"))
        validated_data["other_cost"] = _money(validated_data.get("other_cost"))
        validated_data["total_cost"] = cls.total(
            validated_data["part_cost"],
            validated_data["labor_cost"],
            validated_data["other_cost"],
        )
        validated_data.setdefault("occurred_at", timezone.now())
        validated_data.setdefault("currency", Currency.TRY)
        record = CostRecord(**validated_data)
        record.created_by = actor
        record.updated_by = actor
        record.save()
        return record

    @classmethod
    def update(cls, *, actor, record: CostRecord, validated_data: dict) -> CostRecord:
        for field, value in validated_data.items():
            if field in {"part_cost", "labor_cost", "other_cost"}:
                value = _money(value)
            setattr(record, field, value)
        record.total_cost = cls.total(record.part_cost, record.labor_cost, record.other_cost)
        record.updated_by = actor
        record.save()
        return record

    @classmethod
    def sync_work_order(cls, *, actor, work_order: WorkOrder) -> CostRecord:
        lines = list(work_order.parts.select_related("part").all())
        part_cost = sum((line.quantity * line.unit_cost for line in lines), Decimal("0"))
        record = CostRecord.objects.filter(work_order=work_order).first()
        payload = {
            "work_order": work_order,
            "uav": work_order.uav,
            "component": work_order.component,
            "maintenance_type": work_order.maintenance_type,
            "part_cost": part_cost,
            "currency": (lines[0].part.currency if lines else Currency.TRY),
            "occurred_at": work_order.completed_at or timezone.now(),
        }
        if record is None:
            payload["labor_cost"] = Decimal("0")
            payload["other_cost"] = Decimal("0")
            return cls.create(actor=actor, validated_data=payload)
        return cls.update(
            actor=actor,
            record=record,
            validated_data={
                "part_cost": part_cost,
                "uav": work_order.uav,
                "component": work_order.component,
            },
        )


class WorkOrderPartService:
    @staticmethod
    def is_compatible(*, part: Part, work_order: WorkOrder) -> bool:
        rows = list(part.compatibilities.all())
        if not rows:
            return False
        uav = work_order.uav
        component_type_id = (
            work_order.component.component_type_id if work_order.component_id else None
        )
        for row in rows:
            if component_type_id and row.component_type_id != component_type_id:
                continue
            if row.uav_class_id and row.uav_class_id != uav.uav_class_id:
                continue
            if row.platform_type_id and row.platform_type_id != uav.platform_type_id:
                continue
            return True
        return False

    @classmethod
    def create(cls, *, actor, work_order: WorkOrder, validated_data: dict) -> WorkOrderPart:
        quantity = _money(validated_data.get("quantity"))
        if quantity <= 0:
            raise InvalidPartQuantity()
        part = validated_data["part"]
        if not cls.is_compatible(part=part, work_order=work_order):
            raise PartIncompatible()
        with transaction.atomic():
            locked = Part.objects.select_for_update().get(pk=part.pk)
            if locked.stock_qty < quantity:
                raise InsufficientStock()
            locked.stock_qty = locked.stock_qty - quantity
            locked.updated_by = actor
            locked.save(update_fields=["stock_qty", "updated_by", "updated_at"])
            line = WorkOrderPart(
                work_order=work_order,
                part=locked,
                quantity=quantity,
                unit_cost=validated_data.get("unit_cost") or locked.unit_cost,
            )
            line.created_by = actor
            line.updated_by = actor
            try:
                line.save()
            except IntegrityError as exc:
                raise PartIncompatible() from exc
            CostRecordService.sync_work_order(actor=actor, work_order=work_order)
        return WorkOrderPart.objects.select_related("part").get(pk=line.pk)

    @classmethod
    def delete(cls, *, actor, line: WorkOrderPart) -> None:
        work_order = line.work_order
        with transaction.atomic():
            locked = Part.objects.select_for_update().get(pk=line.part_id)
            locked.stock_qty = locked.stock_qty + line.quantity
            locked.updated_by = actor
            locked.save(update_fields=["stock_qty", "updated_by", "updated_at"])
            line.updated_by = actor
            line.save(update_fields=["updated_by", "updated_at"])
            line.delete()
            CostRecordService.sync_work_order(actor=actor, work_order=work_order)
