from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from django.db.models import QuerySet
from django.utils.dateparse import parse_date

from apps.components.models import UAVComponent
from apps.core.api_exceptions import InvalidReliabilityRange, ReportUavRequired
from apps.failures.models import Failure
from apps.flights.models import Flight
from apps.fmea.models import FMEA
from apps.maintenance.models import MaintenanceRecord, WorkOrder
from apps.parts.models import CostRecord
from apps.rcm.models import RCMAnalysis
from apps.reliability.services import ReliabilityService
from apps.reports.labels import labels_for
from apps.uavs.models import UAV

PDF_ROW_LIMIT = 100
XLSX_ROW_LIMIT = 500


@dataclass
class ReportTable:
    title: str
    headers: list[str]
    rows: list[list[str]]
    demo: bool = False


@dataclass
class ReportDocument:
    filename_stem: str
    title: str
    locale: str
    tables: list[ReportTable] = field(default_factory=list)
    demo: bool = False


def _as_text(value) -> str:
    if value is None:
        return ""
    return str(value)


def _dt(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat(sep=" ", timespec="minutes")
    return str(value)


def _parse_day(value: str | None) -> date | None:
    if not value:
        return None
    parsed = parse_date(value)
    if parsed is None:
        raise InvalidReliabilityRange()
    return parsed


class ReportQuery:
    def __init__(self, params, *, locale: str, limit: int):
        self.uav_id = params.get("uav") or None
        self.scope = params.get("scope") or "fleet"
        self.scope_id = params.get("scope_id") or self.uav_id
        self.class_id = params.get("class") or params.get("uav_class_id") or None
        self.platform_id = params.get("platform") or params.get("platform_type_id") or None
        self.mission_id = params.get("mission") or params.get("mission_type_id") or None
        self.day_from = _parse_day(params.get("from"))
        self.day_to = _parse_day(params.get("to"))
        if self.day_from and self.day_to and self.day_from > self.day_to:
            raise InvalidReliabilityRange()
        self.locale = locale if locale in ("tr", "en", "az") else "tr"
        self.labels = labels_for(self.locale)
        self.limit = limit

    def filter_uav(self, queryset: QuerySet, field: str = "uav_id") -> QuerySet:
        if self.uav_id:
            queryset = queryset.filter(**{field: self.uav_id})
        return queryset

    def filter_day(self, queryset: QuerySet, field: str) -> QuerySet:
        if self.day_from:
            queryset = queryset.filter(**{f"{field}__date__gte": self.day_from})
        if self.day_to:
            queryset = queryset.filter(**{f"{field}__date__lte": self.day_to})
        return queryset


def _table(title: str, headers: list[str], rows: list[list[str]], demo=False) -> ReportTable:
    return ReportTable(title=title, headers=headers, rows=rows, demo=demo)


def _uavs(query: ReportQuery) -> QuerySet:
    queryset = UAV.objects.select_related("uav_class", "platform_type", "mission_type")
    return query.filter_uav(queryset, "id").order_by("registration_number")[: query.limit]


def fleet_table(query: ReportQuery) -> ReportTable:
    labels = query.labels
    rows = []
    demo = False
    for uav in _uavs(query):
        demo = demo or uav.is_demo
        rows.append(
            [
                uav.registration_number,
                uav.serial_number,
                uav.uav_class.code if uav.uav_class_id else "",
                uav.platform_type.code if uav.platform_type_id else "",
                uav.status,
                _as_text(uav.total_flight_hours),
            ]
        )
    return _table(
        labels["fleet"],
        [
            labels["registration"],
            labels["serial"],
            labels["class"],
            labels["platform"],
            labels["status"],
            labels["hours"],
        ],
        rows,
        demo,
    )


def components_table(query: ReportQuery) -> ReportTable:
    labels = query.labels
    queryset = UAVComponent.objects.select_related("uav", "component_type")
    queryset = query.filter_uav(queryset).order_by("uav__registration_number", "name")
    rows = []
    demo = False
    for item in queryset[: query.limit]:
        demo = demo or item.is_demo
        rows.append(
            [
                item.uav.registration_number,
                item.name,
                item.serial_number,
                item.component_type.code if item.component_type_id else "",
                item.status,
                _as_text(item.operating_hours),
            ]
        )
    return _table(
        labels["components"],
        [
            labels["registration"],
            labels["name"],
            labels["serial"],
            labels["type"],
            labels["status"],
            labels["hours"],
        ],
        rows,
        demo,
    )


def flights_table(query: ReportQuery) -> ReportTable:
    labels = query.labels
    queryset = Flight.objects.select_related("uav")
    queryset = query.filter_day(query.filter_uav(queryset), "start_at")
    rows = []
    demo = False
    for item in queryset.order_by("-start_at")[: query.limit]:
        demo = demo or item.is_demo
        rows.append(
            [
                item.flight_number,
                item.uav.registration_number,
                _as_text(item.flown_on),
                _as_text(item.duration_hours),
                item.result,
            ]
        )
    return _table(
        labels["flights"],
        [
            labels["number"],
            labels["registration"],
            labels["date"],
            labels["duration"],
            labels["result"],
        ],
        rows,
        demo,
    )


def work_orders_table(query: ReportQuery) -> ReportTable:
    labels = query.labels
    queryset = WorkOrder.objects.select_related("uav", "assigned_technician__user")
    queryset = query.filter_day(query.filter_uav(queryset), "created_at")
    rows = []
    demo = False
    for item in queryset.order_by("-created_at")[: query.limit]:
        demo = demo or item.is_demo
        assignee = ""
        if item.assigned_technician_id and item.assigned_technician.user_id:
            assignee = item.assigned_technician.user.full_name
        rows.append(
            [
                item.number,
                item.uav.registration_number,
                item.status,
                item.maintenance_type,
                assignee,
            ]
        )
    return _table(
        labels["work_order"],
        [
            labels["number"],
            labels["registration"],
            labels["status"],
            labels["type"],
            labels["assignee"],
        ],
        rows,
        demo,
    )


def maintenance_table(query: ReportQuery) -> ReportTable:
    labels = query.labels
    queryset = MaintenanceRecord.objects.select_related("uav", "work_order", "technician")
    queryset = query.filter_day(query.filter_uav(queryset), "performed_at")
    rows = []
    for item in queryset.order_by("-performed_at")[: query.limit]:
        rows.append(
            [
                _dt(item.performed_at),
                item.uav.registration_number,
                item.work_order.number if item.work_order_id else "",
                item.maintenance_type,
                item.technician.full_name if item.technician_id else "",
            ]
        )
    return _table(
        labels["maintenance"],
        [
            labels["date"],
            labels["registration"],
            labels["number"],
            labels["type"],
            labels["assignee"],
        ],
        rows,
    )


def failures_table(query: ReportQuery) -> ReportTable:
    labels = query.labels
    queryset = Failure.objects.select_related("uav", "failure_mode")
    queryset = query.filter_day(query.filter_uav(queryset), "occurred_at")
    rows = []
    demo = False
    for item in queryset.order_by("-occurred_at")[: query.limit]:
        demo = demo or item.is_demo
        rows.append(
            [
                _dt(item.occurred_at),
                item.uav.registration_number,
                item.failure_mode.code if item.failure_mode_id else "",
                item.severity,
                "resolved" if item.resolved_at else "open",
            ]
        )
    return _table(
        labels["failures"],
        [
            labels["date"],
            labels["registration"],
            labels["mode"],
            labels["severity"],
            labels["status"],
        ],
        rows,
        demo,
    )


def fmea_table(query: ReportQuery) -> ReportTable:
    labels = query.labels
    queryset = FMEA.objects.select_related("uav_class", "platform_type", "component_type")
    rows = []
    demo = False
    for item in queryset.order_by("code")[: query.limit]:
        demo = demo or item.is_demo
        rows.append(
            [
                item.code,
                item.title,
                item.component_type.code if item.component_type_id else "",
                item.status,
                _as_text(item.revision),
            ]
        )
    return _table(
        labels["fmea"],
        [labels["code"], labels["title"], labels["component"], labels["status"], "Rev"],
        rows,
        demo,
    )


def rcm_table(query: ReportQuery) -> ReportTable:
    labels = query.labels
    queryset = RCMAnalysis.objects.select_related("uav_class", "platform_type", "component_type")
    rows = []
    demo = False
    for item in queryset.order_by("code")[: query.limit]:
        demo = demo or item.is_demo
        rows.append(
            [
                item.code,
                item.title,
                item.component_type.code if item.component_type_id else "",
                item.status,
                _as_text(item.revision),
            ]
        )
    return _table(
        labels["rcm"],
        [labels["code"], labels["title"], labels["component"], labels["status"], "Rev"],
        rows,
        demo,
    )


def costs_table(query: ReportQuery) -> ReportTable:
    labels = query.labels
    queryset = CostRecord.objects.select_related("uav", "work_order")
    queryset = query.filter_day(query.filter_uav(queryset), "occurred_at")
    rows = []
    demo = False
    for item in queryset.order_by("-occurred_at")[: query.limit]:
        demo = demo or item.is_demo
        rows.append(
            [
                _dt(item.occurred_at),
                item.uav.registration_number,
                item.work_order.number if item.work_order_id else "",
                _as_text(item.part_cost),
                _as_text(item.labor_cost),
                _as_text(item.total_cost),
                item.currency,
            ]
        )
    return _table(
        labels["costs"],
        [
            labels["date"],
            labels["registration"],
            labels["number"],
            labels["part"],
            labels["labor"],
            labels["total"],
            "CCY",
        ],
        rows,
        demo,
    )


def reliability_table(query: ReportQuery) -> ReportTable:
    labels = query.labels
    data = ReliabilityService.compute(
        scope=query.scope,
        scope_id=query.scope_id,
        period_start=query.day_from.isoformat() if query.day_from else None,
        period_end=query.day_to.isoformat() if query.day_to else None,
    )
    rows = [
        [
            _as_text(data.get("scope_label")),
            _as_text(data.get("mtbf_hours")),
            _as_text(data.get("mttr_hours")),
            _as_text(data.get("availability")),
            _as_text(data.get("failure_count")),
            _as_text(data.get("operating_hours")),
        ]
    ]
    return _table(
        labels["reliability"],
        [
            labels["scope"],
            labels["mtbf"],
            labels["mttr"],
            labels["availability"],
            labels["failures_count"],
            labels["operating"],
        ],
        rows,
    )


def uav_history_tables(query: ReportQuery) -> list[ReportTable]:
    if not query.uav_id:
        raise ReportUavRequired()
    uav = (
        UAV.objects.select_related("uav_class", "platform_type", "mission_type")
        .filter(pk=query.uav_id)
        .first()
    )
    if uav is None:
        raise ReportUavRequired()
    labels = query.labels
    identity = _table(
        labels["identity"],
        [labels["registration"], labels["serial"], labels["class"], labels["hours"]],
        [
            [
                uav.registration_number,
                uav.serial_number,
                uav.uav_class.code if uav.uav_class_id else "",
                _as_text(uav.total_flight_hours),
            ]
        ],
        uav.is_demo,
    )
    return [
        identity,
        flights_table(query),
        work_orders_table(query),
        maintenance_table(query),
        failures_table(query),
        costs_table(query),
    ]


def approach_comparison_tables(query: ReportQuery) -> list[ReportTable]:
    from apps.maintenance.comparison_services import ApproachComparisonService

    labels = query.labels
    data = ApproachComparisonService.compare(
        class_id=query.class_id,
        platform_id=query.platform_id,
        mission_id=query.mission_id,
        period_start=query.day_from.isoformat() if query.day_from else None,
        period_end=query.day_to.isoformat() if query.day_to else None,
    )
    rows = []
    for arm in data["arms"]:
        rows.append(
            [
                arm["approach"],
                _as_text(arm["uav_count"]),
                _as_text(arm["template_count"]),
                _as_text(arm["template_item_count"]),
                _as_text(arm["due_attention"]),
                _as_text(arm["due_overdue"]),
                _as_text(arm["work_order_open"]),
                _as_text(arm["failure_count"]),
                _as_text(arm.get("mtbf_hours")),
                _as_text(arm.get("mttr_hours")),
                _as_text(arm.get("availability")),
                _as_text(arm["cost_total"]),
            ]
        )
    return [
        _table(
            labels["approach_comparison"],
            [
                labels["approach"],
                labels["uav_count"],
                labels["templates"],
                labels["template_items"],
                labels["due_attention"],
                labels["due_overdue"],
                labels["wo_open"],
                labels["failures_count"],
                labels["mtbf"],
                labels["mttr"],
                labels["availability"],
                labels["total"],
            ],
            rows,
            data["is_demo"],
        )
    ]
