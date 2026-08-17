from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
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
    MaintenanceTemplate,
    MaintenanceTemplateItem,
    WorkOrder,
)
from apps.maintenance.services import DEFAULT_DUE_RULES, MaintenanceDueService
from apps.maintenance.work_order_services import WorkOrderService
from apps.notifications.services import NotificationService
from apps.parts.enums import Currency, PartStatus
from apps.parts.models import Part, PartCompatibility, WorkOrderPart
from apps.parts.services import WorkOrderPartService
from apps.rcm.enums import Detectability, RCMStatus
from apps.rcm.models import RCMAnalysis, RCMItem
from apps.rcm.services import RCMService
from apps.uavs.enums import MaintenanceApproach, UAVStatus
from apps.uavs.models import UAV, MissionType, PlatformType, UAVClass

DEMO_NOTE = "DEMO DATA — resmi bakım standardı değildir."

FAILURE_MODES = (
    ("PROP-IMBAL", "Pervane dengesizliği"),
    ("BEAR-WEAR", "Rulman aşınması"),
    ("BATT-DEG", "Batarya bozulması"),
    ("LINK-LOSS", "Komuta bağlantı kaybı"),
)

COMPONENT_TYPES = (
    ("AIRFRAME", "Airframe", True, False),
    ("PROPULSION", "Propulsion", True, True),
    ("AVIONICS", "Avionics", True, False),
    ("BATTERY", "Battery", True, True),
    ("PAYLOAD", "Payload", False, False),
)

CS_ITEMS = (
    (
        "AIRFRAME",
        "AF-VIS-050",
        "Airframe visual inspection",
        Decimal("50"),
        IntervalUnit.FLIGHT_HOURS,
        Priority.MEDIUM,
        InspectionType.VISUAL,
        45,
    ),
    (
        "AIRFRAME",
        "AF-OH-200",
        "Airframe overhaul",
        Decimal("200"),
        IntervalUnit.FLIGHT_HOURS,
        Priority.HIGH,
        InspectionType.OVERHAUL,
        480,
    ),
    (
        "PROPULSION",
        "PR-VIS-025",
        "Propulsion visual inspection",
        Decimal("25"),
        IntervalUnit.FLIGHT_HOURS,
        Priority.HIGH,
        InspectionType.VISUAL,
        30,
    ),
    (
        "BATTERY",
        "BT-CYC-100",
        "Battery cycle check",
        Decimal("100"),
        IntervalUnit.COMPONENT_CYCLES,
        Priority.MEDIUM,
        InspectionType.FUNCTIONAL,
        60,
    ),
    (
        "PAYLOAD",
        "PL-CAL-090",
        "Payload calendar inspection",
        Decimal("90"),
        IntervalUnit.CALENDAR_DAYS,
        Priority.LOW,
        InspectionType.FUNCTIONAL,
        90,
    ),
)

ST_ITEMS = (
    (
        "AIRFRAME",
        "AF-VIS-080",
        "Airframe visual inspection",
        Decimal("80"),
        IntervalUnit.FLIGHT_HOURS,
        Priority.MEDIUM,
        InspectionType.VISUAL,
        45,
    ),
    (
        "PROPULSION",
        "PR-VIS-050",
        "Propulsion visual inspection",
        Decimal("50"),
        IntervalUnit.FLIGHT_HOURS,
        Priority.MEDIUM,
        InspectionType.VISUAL,
        30,
    ),
    (
        "PAYLOAD",
        "PL-CAL-180",
        "Payload calendar inspection",
        Decimal("180"),
        IntervalUnit.CALENDAR_DAYS,
        Priority.LOW,
        InspectionType.FUNCTIONAL,
        90,
    ),
)

UAV_COUNTERS = {
    "TR-UAV-001": (Decimal("45"), 12, 40, 60),
    "TR-UAV-002": (Decimal("110"), 30, 120, 200),
    "TR-UAV-003": (Decimal("18"), 8, 20, 20),
    "TR-UAV-004": (Decimal("24"), 10, 90, 80),
    "TR-UAV-005": (Decimal("80"), 22, 50, 100),
    "TR-UAV-006": (Decimal("45"), 12, 40, 60),
}


class Command(BaseCommand):
    help = "Seed catalog, templates, items, demo components and dues."

    def handle(self, *args, **options):
        SystemSetting.objects.update_or_create(
            key="maintenance.due_rules",
            defaults={
                "value": DEFAULT_DUE_RULES,
                "description": "Due status percent thresholds",
            },
        )
        SystemSetting.objects.update_or_create(
            key="work_order.auto_create_on_due",
            defaults={
                "value": False,
                "description": "Create OPEN work order when due threshold is crossed",
            },
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
            defaults={
                "value": "undefined",
                "description": "undefined | operating_time_as_lower_bound",
            },
        )
        classes = {
            "VERY_LIGHT": self._class("VERY_LIGHT", "Very Light", 0, Decimal("0"), Decimal("2")),
            "LIGHT": self._class("LIGHT", "Light", 1, Decimal("2"), Decimal("25")),
            "MEDIUM": self._class("MEDIUM", "Medium", 2, Decimal("25"), Decimal("150")),
            "HEAVY": self._class("HEAVY", "Heavy", 3, Decimal("150"), Decimal("600")),
        }
        platforms = {
            "FIXED_WING": self._platform("FIXED_WING", "Fixed Wing"),
            "MULTICOPTER": self._platform("MULTICOPTER", "Multicopter"),
            "VTOL": self._platform("VTOL", "VTOL"),
        }
        missions = {
            "MAPPING": self._mission("MAPPING", "Mapping"),
            "SURVEILLANCE": self._mission("SURVEILLANCE", "Surveillance"),
            "INSPECTION": self._mission("INSPECTION", "Inspection"),
        }
        types = {
            code: self._component_type(code, name, hours, cycles)
            for code, name, hours, cycles in COMPONENT_TYPES
        }

        templates = [
            (
                "TPL-FW-MED-MAP-CS",
                "Fixed Wing Medium Mapping",
                "MEDIUM",
                "FIXED_WING",
                "MAPPING",
                "CLASS_SPECIFIC",
            ),
            (
                "TPL-FW-MED-SUR-CS",
                "Fixed Wing Medium Surveillance",
                "MEDIUM",
                "FIXED_WING",
                "SURVEILLANCE",
                "CLASS_SPECIFIC",
            ),
            (
                "TPL-MC-LGT-MAP-CS",
                "Multicopter Light Mapping",
                "LIGHT",
                "MULTICOPTER",
                "MAPPING",
                "CLASS_SPECIFIC",
            ),
            (
                "TPL-MC-LGT-INS-CS",
                "Multicopter Light Inspection",
                "LIGHT",
                "MULTICOPTER",
                "INSPECTION",
                "CLASS_SPECIFIC",
            ),
            (
                "TPL-VT-MED-SUR-CS",
                "VTOL Medium Surveillance",
                "MEDIUM",
                "VTOL",
                "SURVEILLANCE",
                "CLASS_SPECIFIC",
            ),
            (
                "TPL-FW-MED-MAP-ST",
                "Standard Fixed Wing Mapping",
                "MEDIUM",
                "FIXED_WING",
                "MAPPING",
                "STANDARD",
            ),
        ]
        template_map = {}
        for code, name, class_code, platform_code, mission_code, approach in templates:
            template, _ = MaintenanceTemplate.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": DEMO_NOTE,
                    "uav_class": classes[class_code],
                    "platform_type": platforms[platform_code],
                    "mission_type": missions[mission_code],
                    "approach": approach,
                    "is_active": True,
                    "is_demo": True,
                    "notes": DEMO_NOTE,
                },
            )
            template_map[code] = template
            item_defs = ST_ITEMS if approach == "STANDARD" else CS_ITEMS
            self._seed_items(template, types, item_defs)

        now = timezone.now()
        uavs = [
            (
                "TR-UAV-001",
                "SN-FW-001",
                "Acme Aero",
                "AeroMap 200",
                "MEDIUM",
                "FIXED_WING",
                "MAPPING",
                "TPL-FW-MED-MAP-CS",
                MaintenanceApproach.CLASS_SPECIFIC,
            ),
            (
                "TR-UAV-002",
                "SN-FW-002",
                "Acme Aero",
                "AeroWatch 200",
                "MEDIUM",
                "FIXED_WING",
                "SURVEILLANCE",
                "TPL-FW-MED-SUR-CS",
                MaintenanceApproach.CLASS_SPECIFIC,
            ),
            (
                "TR-UAV-003",
                "SN-MC-001",
                "SkyGrid",
                "GridLite 4",
                "LIGHT",
                "MULTICOPTER",
                "MAPPING",
                "TPL-MC-LGT-MAP-CS",
                MaintenanceApproach.CLASS_SPECIFIC,
            ),
            (
                "TR-UAV-004",
                "SN-MC-002",
                "SkyGrid",
                "GridInspect 4",
                "LIGHT",
                "MULTICOPTER",
                "INSPECTION",
                "TPL-MC-LGT-INS-CS",
                MaintenanceApproach.CLASS_SPECIFIC,
            ),
            (
                "TR-UAV-005",
                "SN-VT-001",
                "LiftWing",
                "HybridEye 150",
                "MEDIUM",
                "VTOL",
                "SURVEILLANCE",
                "TPL-VT-MED-SUR-CS",
                MaintenanceApproach.CLASS_SPECIFIC,
            ),
            (
                "TR-UAV-006",
                "SN-FW-006",
                "Acme Aero",
                "AeroMap 200-ST",
                "MEDIUM",
                "FIXED_WING",
                "MAPPING",
                "TPL-FW-MED-MAP-ST",
                MaintenanceApproach.STANDARD,
            ),
        ]
        for row in uavs:
            (
                registration,
                serial,
                manufacturer,
                model,
                class_code,
                platform_code,
                mission_code,
                template_code,
                approach,
            ) = row
            hours, flights, cycles, age_days = UAV_COUNTERS[registration]
            installed_at = now - timedelta(days=age_days)
            uav, _ = UAV.objects.update_or_create(
                registration_number=registration,
                defaults={
                    "serial_number": serial,
                    "manufacturer": manufacturer,
                    "model": model,
                    "uav_class": classes[class_code],
                    "platform_type": platforms[platform_code],
                    "mission_type": missions[mission_code],
                    "maintenance_template": template_map[template_code],
                    "maintenance_approach": approach,
                    "status": UAVStatus.READY,
                    "is_demo": True,
                    "notes": DEMO_NOTE,
                    "total_flight_hours": hours,
                    "total_flight_count": flights,
                    "total_flight_cycles": cycles,
                    "inventory_entry_date": installed_at.date(),
                },
            )
            for type_code, type_name, _hours, _cycles in COMPONENT_TYPES:
                UAVComponent.objects.update_or_create(
                    serial_number=f"{serial}-{type_code[:3]}",
                    defaults={
                        "uav": uav,
                        "component_type": types[type_code],
                        "name": type_name,
                        "part_number": f"PN-{type_code}",
                        "manufacturer": manufacturer,
                        "model": model,
                        "installed_at": installed_at,
                        "operating_hours": hours,
                        "cycle_count": cycles,
                        "status": ComponentStatus.INSTALLED,
                        "is_demo": True,
                        "notes": DEMO_NOTE,
                    },
                )
            MaintenanceDueService.recalculate(uav)

        demo_uav = UAV.objects.filter(registration_number="TR-UAV-001").first()
        operator = User.objects.filter(is_active=True).first()
        if demo_uav:
            start = now - timedelta(hours=7)
            end = now - timedelta(hours=1)
            Flight.objects.update_or_create(
                flight_number="FL-DEMO-001",
                defaults={
                    "uav": demo_uav,
                    "operator": operator,
                    "mission_type": demo_uav.mission_type,
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

        modes = {}
        for code, name in FAILURE_MODES:
            modes[code] = self._failure_mode(code, name)
        self._seed_fmea(classes, platforms, missions, types, modes, operator, now)
        part = self._seed_parts(classes, platforms, types)

        due = MaintenanceDue.objects.filter(
            uav__registration_number="TR-UAV-001",
            template_item__task_code="PR-VIS-025",
        ).first()
        if due and not WorkOrderService.has_open(
            component_id=due.component_id,
            template_item_id=due.template_item_id,
        ):
            work_order = WorkOrderService.create_from_due(actor=operator, due=due)
            work_order.notes = DEMO_NOTE
            work_order.save(update_fields=["notes", "updated_at"])

        if demo_uav:
            propulsion = UAVComponent.objects.filter(
                uav=demo_uav,
                component_type__code="PROPULSION",
            ).first()
            Failure.objects.update_or_create(
                uav=demo_uav,
                failure_mode=modes["PROP-IMBAL"],
                defaults={
                    "component": propulsion,
                    "occurred_at": now - timedelta(hours=12),
                    "discovered_during": DiscoveredDuring.MAINTENANCE,
                    "severity": FailureSeverity.HIGH,
                    "description": "Pervane titreşimi ve dengesizlik şüphesi.",
                    "downtime_hours": Decimal("2.50"),
                    "resolved_at": None,
                    "is_demo": True,
                },
            )
            Failure.objects.update_or_create(
                uav=demo_uav,
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
            demo_wo = WorkOrder.objects.filter(uav=demo_uav, is_demo=True).first()
            if (
                demo_wo
                and part
                and operator
                and not WorkOrderPart.objects.filter(work_order=demo_wo, part=part).exists()
            ):
                WorkOrderPartService.create(
                    actor=operator,
                    work_order=demo_wo,
                    validated_data={"part": part, "quantity": Decimal("1.00")},
                )
            self._seed_documents(demo_uav, demo_wo, operator)
            AuditService.log(
                actor=operator,
                action=AuditAction.UPDATE,
                entity_type="SystemSetting",
                message="Demo seed: system settings initialized",
                new_value={"source": "seed_fleet"},
            )

        alert_dues = MaintenanceDue.objects.filter(
            status__in=[DueStatus.DUE, DueStatus.OVERDUE, DueStatus.CRITICAL]
        ).select_related("uav", "component", "template_item")
        NotificationService.emit_due_changes(
            [(due, None, due.uav, due.component, due.template_item) for due in alert_dues]
        )

        self.stdout.write(self.style.SUCCESS("Fleet seed completed."))

    def _seed_items(self, template, types, item_defs):
        for sequence, row in enumerate(item_defs, start=1):
            (
                type_code,
                task_code,
                task_name,
                interval_value,
                interval_unit,
                priority,
                inspection_type,
                duration,
            ) = row
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
            defaults={
                "name": name,
                "description": DEMO_NOTE,
                "is_demo": True,
                "is_active": True,
            },
        )
        return obj

    def _seed_fmea(self, classes, platforms, missions, types, modes, operator, now):
        fmea, _ = FMEA.objects.update_or_create(
            code="FMEA-FW-MED-PROP-001",
            defaults={
                "title": "Fixed-wing medium propulsion",
                "uav_class": classes["MEDIUM"],
                "platform_type": platforms["FIXED_WING"],
                "component_type": types["PROPULSION"],
                "mission_type": missions["MAPPING"],
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
            code="RCM-FW-MED-PROP-001",
            defaults={
                "title": "Fixed-wing medium propulsion",
                "uav_class": classes["MEDIUM"],
                "platform_type": platforms["FIXED_WING"],
                "component_type": types["PROPULSION"],
                "mission_type": missions["MAPPING"],
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
        RCMService.apply_to_template(actor=operator, analysis=analysis)

    def _seed_parts(self, classes, platforms, types):
        defaults = {
            "name": "Pervane dengeleme kiti",
            "manufacturer": "Acme Aero",
            "model": "BAL-200",
            "min_stock_qty": Decimal("2.00"),
            "unit_cost": Decimal("1500.00"),
            "currency": Currency.TRY,
            "supplier": "AeroParts",
            "location": "Hangar A",
            "status": PartStatus.ACTIVE,
            "is_demo": True,
            "notes": DEMO_NOTE,
        }
        if not Part.objects.filter(part_number="PROP-BAL-001").exists():
            defaults["stock_qty"] = Decimal("4.00")
        part, _ = Part.objects.update_or_create(
            part_number="PROP-BAL-001",
            defaults=defaults,
        )
        PartCompatibility.objects.update_or_create(
            part=part,
            component_type=types["PROPULSION"],
            uav_class=classes["MEDIUM"],
            platform_type=platforms["FIXED_WING"],
            defaults={"is_demo": True},
        )
        return part

    def _seed_documents(self, uav, work_order, operator):
        Document.objects.update_or_create(
            storage_key="DOC-UAV-001-MANUAL",
            defaults={
                "title": "AeroMap 200 uçuş el kitabı",
                "file_name": "aeromap-200-manual.pdf",
                "content_type": "application/pdf",
                "size_bytes": 245760,
                "document_type": DocumentType.MANUAL,
                "uav": uav,
                "uploaded_by": operator,
                "is_demo": True,
                "notes": DEMO_NOTE,
            },
        )
        if work_order:
            Document.objects.update_or_create(
                storage_key="DOC-WO-PROP-PHOTO",
                defaults={
                    "title": "Pervane titreşim fotoğrafı",
                    "file_name": "prop-vibration.jpg",
                    "content_type": "image/jpeg",
                    "size_bytes": 81920,
                    "document_type": DocumentType.PHOTO,
                    "uav": uav,
                    "work_order": work_order,
                    "uploaded_by": operator,
                    "is_demo": True,
                    "notes": DEMO_NOTE,
                },
            )

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
