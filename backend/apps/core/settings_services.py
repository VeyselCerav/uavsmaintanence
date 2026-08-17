from __future__ import annotations

from apps.audit.enums import AuditAction
from apps.audit.services import AuditService
from apps.core.api_exceptions import InvalidDueRules, InvalidSettingValue
from apps.core.models import SystemSetting
from apps.maintenance.services import MaintenanceDueService
from apps.reliability.enums import ZeroFailurePolicy
from apps.uavs.models import UAV

KNOWN_KEYS = (
    "maintenance.due_rules",
    "rpn.thresholds",
    "work_order.auto_create_on_due",
    "reliability.zero_failure_policy",
)

DESCRIPTIONS = {
    "maintenance.due_rules": "Due status percent thresholds",
    "rpn.thresholds": "RPN band thresholds (LOW/MEDIUM/HIGH/CRITICAL)",
    "work_order.auto_create_on_due": "Create OPEN work order when due threshold is crossed",
    "reliability.zero_failure_policy": "undefined | operating_time_as_lower_bound",
}


class SettingsService:
    @classmethod
    def list_payload(cls) -> list[dict]:
        stored = {item.key: item for item in SystemSetting.objects.filter(key__in=KNOWN_KEYS)}
        items = []
        for key in KNOWN_KEYS:
            setting = stored.get(key)
            raw = cls._default_value(key) if setting is None else setting.value
            items.append(
                {
                    "key": key,
                    "value": cls._public_value(key, raw),
                    "description": DESCRIPTIONS[key],
                }
            )
        return items

    @staticmethod
    def _default_value(key: str):
        if key == "maintenance.due_rules":
            return {
                "approaching_percent": 80,
                "due_percent": 100,
                "overdue_percent": 110,
                "critical_percent": 130,
            }
        if key == "rpn.thresholds":
            return {"low_max": 49, "medium_max": 99, "high_max": 199}
        if key == "work_order.auto_create_on_due":
            return False
        return ZeroFailurePolicy.UNDEFINED

    @classmethod
    def _public_value(cls, key: str, raw):
        if key == "maintenance.due_rules":
            if not isinstance(raw, dict):
                return cls._default_value(key)
            return {
                "approaching_percent": float(raw.get("approaching_percent", 80)),
                "due_percent": float(raw.get("due_percent", 100)),
                "overdue_percent": float(raw.get("overdue_percent", 110)),
                "critical_percent": float(raw.get("critical_percent", 130)),
            }
        if key == "rpn.thresholds":
            if not isinstance(raw, dict):
                return cls._default_value(key)
            return {
                "low_max": int(raw.get("low_max", 49)),
                "medium_max": int(raw.get("medium_max", 99)),
                "high_max": int(raw.get("high_max", 199)),
            }
        if key == "work_order.auto_create_on_due":
            return bool(raw)
        if isinstance(raw, dict):
            return raw.get("policy", ZeroFailurePolicy.UNDEFINED)
        return raw

    @classmethod
    def update(cls, *, actor, key: str, value, request=None) -> dict:
        if key not in KNOWN_KEYS:
            raise InvalidSettingValue()
        normalized = cls._normalize(key, value)
        setting = SystemSetting.objects.filter(key=key).first()
        old_value = setting.value if setting else None
        SystemSetting.objects.update_or_create(
            key=key,
            defaults={
                "value": normalized,
                "description": DESCRIPTIONS[key],
                "updated_by": actor,
            },
        )
        if key == "maintenance.due_rules":
            for uav in UAV.objects.all():
                MaintenanceDueService.recalculate(uav)
        AuditService.log(
            actor=actor,
            action=AuditAction.UPDATE,
            entity_type="SystemSetting",
            entity_id=setting.id if setting else None,
            old_value={"key": key, "value": old_value},
            new_value={"key": key, "value": normalized},
            request=request,
        )
        return {"key": key, "value": normalized, "description": DESCRIPTIONS[key]}

    @classmethod
    def _normalize(cls, key: str, value):
        if key == "maintenance.due_rules":
            if not isinstance(value, dict):
                raise InvalidSettingValue()
            approaching = value.get("approaching_percent")
            due = value.get("due_percent")
            overdue = value.get("overdue_percent")
            critical = value.get("critical_percent")
            try:
                rules = {
                    "approaching_percent": float(approaching),
                    "due_percent": float(due),
                    "overdue_percent": float(overdue),
                    "critical_percent": float(critical),
                }
            except (TypeError, ValueError) as exc:
                raise InvalidSettingValue() from exc
            if not (
                0
                < rules["approaching_percent"]
                < rules["due_percent"]
                < rules["overdue_percent"]
                < rules["critical_percent"]
            ):
                raise InvalidDueRules()
            return rules
        if key == "rpn.thresholds":
            if not isinstance(value, dict):
                raise InvalidSettingValue()
            try:
                low = int(value["low_max"])
                medium = int(value["medium_max"])
                high = int(value["high_max"])
            except (TypeError, ValueError, KeyError) as exc:
                raise InvalidSettingValue() from exc
            if not (0 < low < medium < high):
                raise InvalidSettingValue()
            return {"low_max": low, "medium_max": medium, "high_max": high}
        if key == "work_order.auto_create_on_due":
            if isinstance(value, bool):
                return value
            raise InvalidSettingValue()
        if key == "reliability.zero_failure_policy":
            if isinstance(value, dict):
                value = value.get("policy")
            if value not in ZeroFailurePolicy.values:
                raise InvalidSettingValue()
            return value
        raise InvalidSettingValue()
