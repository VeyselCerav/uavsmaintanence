from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.components.enums import ComponentStatus
from apps.components.models import ComponentType, UAVComponent
from apps.core.models import SystemSetting
from apps.maintenance.enums import DueStatus, InspectionType, IntervalUnit, Priority
from apps.maintenance.models import MaintenanceDue, MaintenanceTemplate, MaintenanceTemplateItem
from apps.maintenance.services import MaintenanceDueService
from apps.technicians.models import Technician
from apps.uavs.models import UAV, MissionType, PlatformType, UAVClass


@pytest.fixture
def rbac(db):
    call_command("seed_rbac")


def _user(email: str, role_code: str, password: str = "secret12345") -> User:
    role = Role.objects.get(code=role_code)
    return User.objects.create_user(
        email=email,
        password=password,
        full_name=role_code,
        role=role,
        is_active=True,
    )


def _auth_client(user: User, password: str = "secret12345") -> APIClient:
    client = APIClient()
    response = client.post(
        "/api/v1/auth/login/",
        {"email": user.email, "password": password},
        format="json",
    )
    assert response.status_code == 200
    token = response.json()["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def catalog(db):
    uav_class = UAVClass.objects.create(code="MEDIUM", name="Medium")
    platform = PlatformType.objects.create(code="FIXED_WING", name="Fixed Wing")
    mission = MissionType.objects.create(code="MAPPING", name="Mapping")
    airframe = ComponentType.objects.create(code="AIRFRAME", name="Airframe")
    template = MaintenanceTemplate.objects.create(
        code="TPL-WO",
        name="WO test template",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        approach="CLASS_SPECIFIC",
    )
    item = MaintenanceTemplateItem.objects.create(
        template=template,
        component_type=airframe,
        sequence=1,
        task_code="AF-VIS-050",
        task_name="Airframe visual",
        interval_value=Decimal("50"),
        interval_unit=IntervalUnit.FLIGHT_HOURS,
        priority=Priority.HIGH,
        inspection_type=InspectionType.VISUAL,
    )
    uav = UAV.objects.create(
        registration_number="TR-WO-001",
        serial_number="SN-WO-001",
        manufacturer="TestCo",
        model="T-WO",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        maintenance_template=template,
        maintenance_approach="CLASS_SPECIFIC",
        total_flight_hours=Decimal("51"),
        total_flight_cycles=11,
    )
    UAVComponent.objects.create(
        uav=uav,
        component_type=airframe,
        name="Airframe",
        serial_number="SN-WO-AF",
        operating_hours=Decimal("51"),
        cycle_count=11,
        status=ComponentStatus.INSTALLED,
    )
    dues = MaintenanceDueService.recalculate(uav)
    return {"uav": uav, "item": item, "due": dues[0]}


@pytest.mark.django_db
def test_work_order_lifecycle_resets_due(rbac, catalog):
    manager = _user("mgr-wo@test.local", "MAINTENANCE_MANAGER")
    tech_user = _user("tech-wo@test.local", "TECHNICIAN")
    technician = Technician.objects.create(user=tech_user, employee_number="EMP-WO-1")
    client = _auth_client(manager)
    created = client.post("/api/v1/work-orders/", {"due": str(catalog["due"].id)}, format="json")
    assert created.status_code == 201
    work_id = created.json()["data"]["id"]
    assert created.json()["data"]["status"] == "OPEN"

    duplicate = client.post("/api/v1/work-orders/", {"due": str(catalog["due"].id)}, format="json")
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "WORK_ORDER_ALREADY_OPEN"

    invalid = client.post(f"/api/v1/work-orders/{work_id}/complete/", format="json")
    assert invalid.status_code == 409
    assert invalid.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"

    assigned = client.post(
        f"/api/v1/work-orders/{work_id}/assign/",
        {"assigned_technician": str(technician.id)},
        format="json",
    )
    assert assigned.status_code == 200
    assert assigned.json()["data"]["status"] == "ASSIGNED"

    from apps.notifications.enums import NotificationType
    from apps.notifications.models import Notification

    tech_notes = Notification.objects.filter(
        user=tech_user,
        type=NotificationType.WORK_ORDER_ASSIGNED,
    )
    assert tech_notes.count() == 1
    assert tech_notes.get().payload["work_order_id"] == work_id
    assert Notification.objects.filter(user=manager, type=NotificationType.WORK_ORDER_ASSIGNED).count() == 0

    assigned_again = client.post(
        f"/api/v1/work-orders/{work_id}/assign/",
        {"assigned_technician": str(technician.id)},
        format="json",
    )
    assert assigned_again.status_code == 200
    assert tech_notes.count() == 1

    started = client.post(f"/api/v1/work-orders/{work_id}/start/", format="json")
    assert started.status_code == 200
    assert started.json()["data"]["status"] == "IN_PROGRESS"

    completed = client.post(f"/api/v1/work-orders/{work_id}/complete/", format="json")
    assert completed.status_code == 200
    assert completed.json()["data"]["status"] == "COMPLETED"

    done_notes = Notification.objects.filter(
        user=manager,
        type=NotificationType.WORK_ORDER_COMPLETED,
    )
    assert done_notes.count() == 1
    assert done_notes.get().payload["work_order_id"] == work_id
    assert Notification.objects.filter(user=tech_user, type=NotificationType.WORK_ORDER_COMPLETED).count() == 0

    due = MaintenanceDue.objects.get(pk=catalog["due"].id)
    assert due.status == DueStatus.NORMAL
    assert due.usage_percent == Decimal("0.00")

    history = client.get("/api/v1/maintenance-records/")
    assert history.status_code == 200
    rows = history.json()["data"]
    assert len(rows) == 1
    assert rows[0]["work_order"] == work_id
    assert rows[0]["uav_registration"] == "TR-WO-001"
    assert rows[0]["task_code"] == "AF-VIS-050"
    found = client.get("/api/v1/maintenance-records/?search=TR-WO")
    assert len(found.json()["data"]) == 1
    missed = client.get("/api/v1/maintenance-records/?search=NOPE")
    assert len(missed.json()["data"]) == 0
    by_uav = client.get(f"/api/v1/maintenance-records/?uav={catalog['uav'].id}")
    assert len(by_uav.json()["data"]) == 1


@pytest.mark.django_db
def test_auto_create_on_due(rbac, catalog):
    SystemSetting.objects.update_or_create(
        key="work_order.auto_create_on_due",
        defaults={"value": True},
    )
    MaintenanceDueService.recalculate(catalog["uav"])
    from apps.maintenance.models import WorkOrder

    assert WorkOrder.objects.filter(uav=catalog["uav"], status="OPEN").count() == 1


@pytest.mark.django_db
def test_viewer_can_list_maintenance_records(rbac):
    client = _auth_client(_user("viewer-rec@test.local", "VIEWER"))
    response = client.get("/api/v1/maintenance-records/")
    assert response.status_code == 200
    assert response.json()["data"] == []


@pytest.mark.django_db
def test_viewer_cannot_create_work_order(rbac, catalog):
    client = _auth_client(_user("viewer-wo@test.local", "VIEWER"))
    response = client.post("/api/v1/work-orders/", {"due": str(catalog["due"].id)}, format="json")
    assert response.status_code == 403
