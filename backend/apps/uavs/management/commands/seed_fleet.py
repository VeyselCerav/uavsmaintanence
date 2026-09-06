from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.enums import AuditAction
from apps.audit.services import AuditService
from apps.components.enums import ComponentStatus
from apps.components.models import ComponentType, UAVComponent
from apps.core.models import SystemSetting
from apps.documents.enums import DocumentType
from apps.documents.models import Document
from apps.failures.enums import DiscoveredDuring, FailureSeverity
from apps.failures.models import Failure, FailureMode
from apps.flights.enums import FlightResult
from apps.flights.models import Flight
from apps.fmea.enums import FMEAStatus
from apps.fmea.models import FMEA, FMEAItem
from apps.maintenance.enums import DueStatus, InspectionType, IntervalUnit, Priority, RCMStrategy
from apps.maintenance.models import (
    MaintenanceDue,
    MaintenanceRecord,
    MaintenanceTemplate,
    MaintenanceTemplateItem,
    WorkOrder,
)
from apps.maintenance.services import DEFAULT_DUE_RULES, MaintenanceDueService
from apps.maintenance.work_order_services import WorkOrderService
from apps.notifications.services import NotificationService
from apps.parts.enums import Currency, PartStatus
from apps.parts.models import CostRecord, Part, PartCompatibility, WorkOrderPart
from apps.parts.services import WorkOrderPartService
from apps.rcm.enums import Detectability, RCMStatus
from apps.rcm.models import RCMAnalysis, RCMItem
from apps.rcm.services import RCMService
from apps.uavs.enums import MaintenanceApproach, UAVStatus
from apps.uavs.models import UAV, MissionType, PlatformType, UAVClass

DEMO_NOTE = "Açık kaynak derleme — resmi bakım standardı değildir."
CATALOG_VERSION = "open-source-v1"
SETTING_KEY = "fleet.catalog_version"
CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "iha-katalog-acik-kaynak.json"
ICE_MODELS = {"Integrator", "Camcopter S-100", "Bayraktar TB2"}
ANCHOR_REGISTRATION = "TR-PUB-007"

FAILURE_MODES = (
    ("PROP-IMBAL", "Pervane dengesizliği"),
    ("BEAR-WEAR", "Rulman aşınması"),
    ("BATT-DEG", "Batarya bozulması"),
    ("LINK-LOSS", "Komuta bağlantı kaybı"),
)

CS_ITEMS = (
    (
        "AIRFRAME",
        "AF-VIS-050",
        "Gövde görsel muayene",
        Decimal("50"),
        IntervalUnit.FLIGHT_HOURS,
        Priority.MEDIUM,
        InspectionType.VISUAL,
        45,
    ),
    (
        "PROPULSION",
        "PR-VIS-025",
        "İtki görsel muayene",
        Decimal("25"),
        IntervalUnit.FLIGHT_HOURS,
        Priority.HIGH,
        InspectionType.VISUAL,
        30,
    ),
    (
        "BATTERY",
        "BT-CYC-100",
        "Batarya çevrim kontrolü",
        Decimal("100"),
        IntervalUnit.COMPONENT_CYCLES,
        Priority.MEDIUM,
        InspectionType.FUNCTIONAL,
        60,
    ),
    (
        "PAYLOAD",
        "PL-CAL-090",
        "Yük takvimli muayene",
        Decimal("90"),
        IntervalUnit.CALENDAR_DAYS,
        Priority.LOW,
        InspectionType.FUNCTIONAL,
        90,
    ),
    (
        "FUEL_SYSTEM",
        "FU-VIS-050",
        "Yakıt sistemi görsel muayene",
        Decimal("50"),
        IntervalUnit.FLIGHT_HOURS,
        Priority.MEDIUM,
        InspectionType.VISUAL,
        40,
    ),
)

ST_ITEMS = (
    (
        "AIRFRAME",
        "AF-VIS-080",
        "Gövde görsel muayene",
        Decimal("80"),
        IntervalUnit.FLIGHT_HOURS,
        Priority.MEDIUM,
        InspectionType.VISUAL,
        45,
    ),
    (
        "PROPULSION",
        "PR-VIS-050",
        "İtki görsel muayene",
        Decimal("50"),
        IntervalUnit.FLIGHT_HOURS,
        Priority.MEDIUM,
        InspectionType.VISUAL,
        30,
    ),
    (
        "PAYLOAD",
        "PL-CAL-180",
        "Yük takvimli muayene",
        Decimal("180"),
        IntervalUnit.CALENDAR_DAYS,
        Priority.LOW,
        InspectionType.FUNCTIONAL,
        90,
    ),
)

COUNTERS = {
    "TR-PUB-001": (Decimal("12"), 6, 10, 40),
    "TR-PUB-002": (Decimal("8"), 4, 8, 30),
    "TR-PUB-003": (Decimal("22"), 10, 18, 70),
    "TR-PUB-004": (Decimal("35"), 14, 28, 90),
    "TR-PUB-005": (Decimal("18"), 8, 14, 50),
    "TR-PUB-006": (Decimal("20"), 9, 16, 55),
    "TR-PUB-007": (Decimal("42"), 20, 80, 80),
    "TR-PUB-008": (Decimal("28"), 40, 60, 45),
    "TR-PUB-009": (Decimal("90"), 24, 40, 200),
    "TR-PUB-010": (Decimal("70"), 18, 30, 150),
    "TR-PUB-011": (Decimal("160"), 40, 50, 400),
}


class Command(BaseCommand):
    help = "Delete mock AeroMap fleet and load the open-source UAV catalog."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-import even if catalog version is already applied.",
        )

    def handle(self, *args, **options):
        current = SystemSetting.objects.filter(key=SETTING_KEY).first()
        if (
            not options["force"]
            and current
            and current.value.get("version") == CATALOG_VERSION
            and UAV.objects.filter(registration_number=ANCHOR_REGISTRATION).exists()
            and not UAV.objects.filter(registration_number="TR-UAV-001").exists()
        ):
            self.stdout.write("Açık kaynak filo zaten yüklü; atlandı (--force ile yenilenir).")
            return

        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        with transaction.atomic():
            self._purge_mock_fleet()
            self._seed_settings()
            self._seed_from_catalog(catalog)

        SystemSetting.objects.update_or_create(
            key=SETTING_KEY,
            defaults={
                "value": {"version": CATALOG_VERSION, "source": str(CATALOG_PATH.name)},
                "description": "Loaded open-source UAV catalog version",
            },
        )
        self.stdout.write(self.style.SUCCESS("Açık kaynak filo yüklendi; eski mock kayıtlar silindi."))

    def _purge_mock_fleet(self):
        demo_uavs = UAV.objects.filter(is_demo=True)
        MaintenanceDue.objects.filter(uav__in=demo_uavs).delete()
        MaintenanceRecord.objects.filter(uav__in=demo_uavs).delete()
        WorkOrderPart.objects.filter(work_order__uav__in=demo_uavs).delete()
        CostRecord.objects.filter(uav__in=demo_uavs).delete()
        Document.objects.filter(is_demo=True).delete()
        Failure.objects.filter(is_demo=True).delete()
        Flight.objects.filter(is_demo=True).delete()
        WorkOrder.objects.filter(is_demo=True).delete()
        UAVComponent.objects.filter(is_demo=True).delete()
        demo_uavs.delete()
        MaintenanceTemplateItem.objects.filter(is_demo=True).delete()
        MaintenanceTemplate.objects.filter(is_demo=True).delete()
        FMEA.objects.filter(is_demo=True).delete()
        RCMAnalysis.objects.filter(is_demo=True).delete()

    def _seed_settings(self):
        SystemSetting.objects.update_or_create(
            key="maintenance.due_rules",
            defaults={"value": DEFAULT_DUE_RULES, "description": "Due status percent thresholds"},
        )
        SystemSetting.objects.update_or_create(
            key="work_order.auto_create_on_due",
            defaults={"value": False, "description": "Create OPEN work order when due threshold is crossed"},
        )
        SystemSetting.objects.update_or_create(
            key="rpn.thresholds",
            defaults={
                "value": {"low_max": 49, "medium_max": 99, "high_max": 199},
                "description": "RPN band thresholds (LOW/MEDIUM/HIGH/CRITICAL)",
            },
        )
        SystemSetting.objects.update_or_create(
            key="reliability.zero_failure_policy",
            defaults={"value": "undefined", "description": "undefined | operating_time_as_lower_bound"},
        )

    def _seed_from_catalog(self, catalog: dict):
        now = timezone.now()
        classes = {}
        for row in catalog["catalog"]["uav_classes"]:
            classes[row["code"]] = self._class(
                row["code"],
                row["name"],
                row["sort_order"],
                Decimal(row["mtow_min_kg"]),
                Decimal(row["mtow_max_kg"]),
            )
        platforms = {
            row["code"]: self._platform(row["code"], row["name"])
            for row in catalog["catalog"]["platform_types"]
        }
        missions = {
            row["code"]: self._mission(row["code"], row["name"])
            for row in catalog["catalog"]["mission_types"]
        }
        types = {
            row["code"]: self._component_type(
                row["code"],
                row["name"],
                row["tracks_hours"],
                row["tracks_cycles"],
            )
            for row in catalog["catalog"]["component_types"]
        }

        template_map = {}
        for uav_row in catalog["uavs"]:
            key = (
                uav_row["uav_class_code"],
                uav_row["platform_type_code"],
                uav_row["mission_type_code"],
                uav_row["maintenance_approach"],
            )
            if key in template_map:
                continue
            approach = uav_row["maintenance_approach"]
            code = self._template_code(*key)
            template, _ = MaintenanceTemplate.objects.update_or_create(
                code=code,
                defaults={
                    "name": f"{uav_row['platform_type_code']} {uav_row['uav_class_code']} {uav_row['mission_type_code']}",
                    "description": DEMO_NOTE,
                    "uav_class": classes[uav_row["uav_class_code"]],
                    "platform_type": platforms[uav_row["platform_type_code"]],
                    "mission_type": missions[uav_row["mission_type_code"]],
                    "approach": approach,
                    "is_active": True,
                    "is_demo": True,
                    "notes": DEMO_NOTE,
                },
            )
            item_defs = ST_ITEMS if approach == MaintenanceApproach.STANDARD else CS_ITEMS
            ice = any(
                item["model"] in ICE_MODELS
                and item["uav_class_code"] == key[0]
                and item["platform_type_code"] == key[1]
                and item["mission_type_code"] == key[2]
                and item["maintenance_approach"] == key[3]
                for item in catalog["uavs"]
            )
            filtered = [
                item
                for item in item_defs
                if not (item[0] == "BATTERY" and ice) and not (item[0] == "FUEL_SYSTEM" and not ice)
            ]
            self._seed_items(template, types, filtered)
            template_map[key] = template

        created = []
        for uav_row in catalog["uavs"]:
            created.append(self._seed_uav(uav_row, classes, platforms, missions, types, template_map, now))

        operator = User.objects.filter(is_active=True).first()
        modes = {code: self._failure_mode(code, name) for code, name in FAILURE_MODES}
        self._seed_fmea(classes, platforms, missions, types, modes, operator, now)
        part = self._seed_parts(classes, platforms, types)

        anchor = UAV.objects.filter(registration_number=ANCHOR_REGISTRATION).first()
        if anchor:
            self._seed_anchor_ops(anchor, modes, part, operator, now)

        alert_dues = MaintenanceDue.objects.filter(
            status__in=[DueStatus.DUE, DueStatus.OVERDUE, DueStatus.CRITICAL]
        ).select_related("uav", "component", "template_item")
        NotificationService.emit_due_changes(
            [(due, None, due.uav, due.component, due.template_item) for due in alert_dues]
        )
        if operator:
            AuditService.log(
                actor=operator,
                action=AuditAction.UPDATE,
                entity_type="SystemSetting",
                message="Open-source fleet catalog loaded",
                new_value={"version": CATALOG_VERSION, "uavs": len(created)},
            )

    def _seed_uav(self, uav_row, classes, platforms, missions, types, template_map, now):
        registration = uav_row["suggested_registration"]
        hours, flights, cycles, age_days = COUNTERS.get(
            registration, (Decimal("15"), 6, 12, 40)
        )
        installed_at = now - timedelta(days=age_days)
        key = (
            uav_row["uav_class_code"],
            uav_row["platform_type_code"],
            uav_row["mission_type_code"],
            uav_row["maintenance_approach"],
        )
        ice = uav_row["model"] in ICE_MODELS
        sources = "; ".join(uav_row.get("sources") or [])
        uav, _ = UAV.objects.update_or_create(
            registration_number=registration,
            defaults={
                "serial_number": uav_row["serial_number"],
                "manufacturer": uav_row["manufacturer"],
                "model": uav_row["model"],
                "uav_class": classes[uav_row["uav_class_code"]],
                "platform_type": platforms[uav_row["platform_type_code"]],
                "mission_type": missions[uav_row["mission_type_code"]],
                "maintenance_template": template_map[key],
                "maintenance_approach": uav_row["maintenance_approach"],
                "mtow_kg": Decimal(uav_row["mtow_kg"]),
                "status": UAVStatus.READY,
                "is_demo": True,
                "notes": f"{uav_row.get('notes') or DEMO_NOTE}\nKaynak: {sources}",
                "total_flight_hours": hours,
                "total_flight_count": flights,
                "total_flight_cycles": cycles,
                "inventory_entry_date": installed_at.date(),
            },
        )
        type_codes = ["AIRFRAME", "PROPULSION", "AVIONICS", "PAYLOAD"]
        if ice:
            type_codes.append("FUEL_SYSTEM")
        else:
            type_codes.append("BATTERY")
        serial = uav_row["serial_number"]
        for type_code in type_codes:
            component_type = types[type_code]
            UAVComponent.objects.update_or_create(
                serial_number=f"{serial}-{type_code[:3]}",
                defaults={
                    "uav": uav,
                    "component_type": component_type,
                    "name": component_type.name,
                    "part_number": f"PN-{type_code}",
                    "manufacturer": uav_row["manufacturer"],
                    "model": uav_row["model"],
                    "installed_at": installed_at,
                    "operating_hours": hours,
                    "cycle_count": cycles,
                    "status": ComponentStatus.INSTALLED,
                    "is_demo": True,
                    "notes": DEMO_NOTE,
                },
            )
        MaintenanceDueService.recalculate(uav)
        return uav

    def _seed_anchor_ops(self, uav, modes, part, operator, now):
        start = now - timedelta(hours=7)
        end = now - timedelta(hours=1)
        Flight.objects.update_or_create(
            flight_number="FL-M350-001",
            defaults={
                "uav": uav,
                "operator": operator,
                "mission_type": uav.mission_type,
                "flown_on": start.date(),
                "start_at": start,
                "end_at": end,
                "duration_hours": Decimal("6.00"),
                "result": FlightResult.COMPLETED,
                "counters_applied": False,
                "is_demo": True,
                "notes": DEMO_NOTE,
            },
        )
        due = MaintenanceDue.objects.filter(
            uav=uav,
            template_item__task_code="PR-VIS-025",
        ).first()
        work_order = None
        if due and operator and not WorkOrderService.has_open(
            component_id=due.component_id,
            template_item_id=due.template_item_id,
        ):
            work_order = WorkOrderService.create_from_due(actor=operator, due=due)
            work_order.notes = DEMO_NOTE
            work_order.save(update_fields=["notes", "updated_at"])
        propulsion = UAVComponent.objects.filter(uav=uav, component_type__code="PROPULSION").first()
        Failure.objects.update_or_create(
            uav=uav,
            failure_mode=modes["PROP-IMBAL"],
            defaults={
                "component": propulsion,
                "occurred_at": now - timedelta(hours=12),
                "discovered_during": DiscoveredDuring.MAINTENANCE,
                "severity": FailureSeverity.HIGH,
                "description": "Pervane titreşimi (Matrice 350 RTK demo kaydı).",
                "downtime_hours": Decimal("2.50"),
                "resolved_at": None,
                "is_demo": True,
            },
        )
        Failure.objects.update_or_create(
            uav=uav,
            failure_mode=modes["BEAR-WEAR"],
            defaults={
                "component": propulsion,
                "occurred_at": now - timedelta(days=10),
                "discovered_during": DiscoveredDuring.FLIGHT,
                "severity": FailureSeverity.MEDIUM,
                "description": "Çözülmüş rulman arızası (demo).",
                "downtime_hours": Decimal("2.50"),
                "resolved_at": now - timedelta(days=9),
                "is_demo": True,
            },
        )
        if work_order and part and operator and not WorkOrderPart.objects.filter(
            work_order=work_order, part=part
        ).exists():
            WorkOrderPartService.create(
                actor=operator,
                work_order=work_order,
                validated_data={"part": part, "quantity": Decimal("1.00")},
            )
        Document.objects.update_or_create(
            storage_key="DOC-M350-SPEC",
            defaults={
                "title": "DJI Matrice 350 RTK teknik özet",
                "file_name": "matrice-350-rtk-specs.pdf",
                "content_type": "application/pdf",
                "size_bytes": 245760,
                "document_type": DocumentType.MANUAL,
                "uav": uav,
                "uploaded_by": operator,
                "is_demo": True,
                "notes": DEMO_NOTE,
            },
        )

    def _seed_items(self, template, types, item_defs):
        for sequence, row in enumerate(item_defs, start=1):
            type_code, task_code, task_name, interval_value, interval_unit, priority, inspection_type, duration = row
            MaintenanceTemplateItem.objects.update_or_create(
                template=template,
                component_type=types[type_code],
                task_code=task_code,
                defaults={
                    "sequence": sequence,
                    "task_name": task_name,
                    "interval_value": interval_value,
                    "interval_unit": interval_unit,
                    "priority": priority,
                    "estimated_duration_minutes": duration,
                    "inspection_type": inspection_type,
                    "rcm_strategy": RCMStrategy.SCHEDULED_INSPECTION,
                    "notes": DEMO_NOTE,
                    "is_demo": True,
                },
            )

    def _template_code(self, class_code, platform_code, mission_code, approach):
        suffix = "ST" if approach == MaintenanceApproach.STANDARD else "CS"
        return f"TPL-{platform_code[:3]}-{class_code[:3]}-{mission_code[:3]}-{suffix}"

    def _component_type(self, code, name, tracks_hours, tracks_cycles):
        obj, _ = ComponentType.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "description": DEMO_NOTE,
                "tracks_hours": tracks_hours,
                "tracks_cycles": tracks_cycles,
                "is_demo": True,
                "is_active": True,
            },
        )
        return obj

    def _failure_mode(self, code, name):
        obj, _ = FailureMode.objects.update_or_create(
            code=code,
            defaults={"name": name, "description": DEMO_NOTE, "is_demo": True, "is_active": True},
        )
        return obj

    def _seed_fmea(self, classes, platforms, missions, types, modes, operator, now):
        fmea, _ = FMEA.objects.update_or_create(
            code="FMEA-MC-LGT-PROP-001",
            defaults={
                "title": "Multicopter light propulsion",
                "uav_class": classes["LIGHT"],
                "platform_type": platforms["MULTICOPTER"],
                "component_type": types["PROPULSION"],
                "mission_type": missions["INSPECTION"],
                "status": FMEAStatus.APPROVED,
                "revision": 1,
                "approved_at": now,
                "approved_by": operator,
                "is_demo": True,
                "notes": DEMO_NOTE,
            },
        )
        fmea_item, _ = FMEAItem.objects.update_or_create(
            fmea=fmea,
            sequence=1,
            defaults={
                "function": "İtki üretmek",
                "functional_failure": "İtki kaybı",
                "failure_mode": "Pervane dengesizliği",
                "catalog_mode": modes["PROP-IMBAL"],
                "failure_cause": "Aşınma veya montaj hatası",
                "failure_effect": "Titreşim ve kontrol kaybı riski",
                "severity": 8,
                "occurrence": 5,
                "detection": 4,
                "rpn": 160,
                "existing_control": "Görsel muayene",
                "recommended_action": "Dengeleme ve periyodik kontrol",
                "is_demo": True,
            },
        )
        self._seed_rcm(classes, platforms, missions, types, fmea_item, operator, now)

    def _seed_rcm(self, classes, platforms, missions, types, fmea_item, operator, now):
        analysis, _ = RCMAnalysis.objects.update_or_create(
            code="RCM-MC-LGT-PROP-001",
            defaults={
                "title": "Multicopter light propulsion",
                "uav_class": classes["LIGHT"],
                "platform_type": platforms["MULTICOPTER"],
                "component_type": types["PROPULSION"],
                "mission_type": missions["INSPECTION"],
                "status": RCMStatus.APPROVED,
                "revision": 1,
                "approved_at": now,
                "approved_by": operator,
                "is_demo": True,
                "notes": DEMO_NOTE,
            },
        )
        RCMItem.objects.update_or_create(
            analysis=analysis,
            sequence=1,
            defaults={
                "function": "İtki üretmek",
                "functional_failure": "İtki kaybı",
                "failure_mode": "Pervane dengesizliği",
                "failure_effect": "Titreşim ve kontrol kaybı riski",
                "safety_effect": False,
                "operational_effect": True,
                "detectability": Detectability.HIGH,
                "preventive_feasible": True,
                "suggested_strategy": RCMStrategy.CONDITION_INSPECTION,
                "strategy": RCMStrategy.CONDITION_INSPECTION,
                "is_overridden": False,
                "rationale": "",
                "fmea_item": fmea_item,
                "is_demo": True,
            },
        )
        if operator:
            RCMService.apply_to_template(actor=operator, analysis=analysis)

    def _seed_parts(self, classes, platforms, types):
        defaults = {
            "name": "Pervane dengeleme kiti",
            "manufacturer": "DJI",
            "model": "2110s",
            "min_stock_qty": Decimal("2.00"),
            "unit_cost": Decimal("1500.00"),
            "currency": Currency.TRY,
            "supplier": "Enterprise Parts",
            "location": "Hangar A",
            "status": PartStatus.ACTIVE,
            "is_demo": True,
            "notes": DEMO_NOTE,
        }
        if not Part.objects.filter(part_number="PROP-BAL-001").exists():
            defaults["stock_qty"] = Decimal("4.00")
        part, _ = Part.objects.update_or_create(part_number="PROP-BAL-001", defaults=defaults)
        PartCompatibility.objects.update_or_create(
            part=part,
            component_type=types["PROPULSION"],
            uav_class=classes["LIGHT"],
            platform_type=platforms["MULTICOPTER"],
            defaults={"is_demo": True},
        )
        return part

    def _class(self, code, name, sort_order, mtow_min, mtow_max):
        obj, _ = UAVClass.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "description": DEMO_NOTE,
                "mtow_min_kg": mtow_min,
                "mtow_max_kg": mtow_max,
                "sort_order": sort_order,
                "is_demo": True,
                "is_active": True,
            },
        )
        return obj

    def _platform(self, code, name):
        obj, _ = PlatformType.objects.update_or_create(
            code=code,
            defaults={"name": name, "description": DEMO_NOTE, "is_demo": True, "is_active": True},
        )
        return obj

    def _mission(self, code, name):
        obj, _ = MissionType.objects.update_or_create(
            code=code,
            defaults={"name": name, "description": DEMO_NOTE, "is_demo": True, "is_active": True},
        )
        return obj
