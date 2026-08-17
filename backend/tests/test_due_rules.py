from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.components.enums import ComponentStatus
from apps.components.models import ComponentType, UAVComponent
from apps.maintenance.enums import DueStatus, InspectionType, IntervalUnit, Priority
from apps.maintenance.models import MaintenanceDue, MaintenanceTemplate, MaintenanceTemplateItem
from apps.maintenance.services import MaintenanceDueService
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
        code="TPL-RULES",
        name="Rules test template",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        approach="CLASS_SPECIFIC",
    )
    MaintenanceTemplateItem.objects.create(
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
        registration_number="TR-RULE-001",
        serial_number="SN-RULE-001",
        manufacturer="TestCo",
        model="T-RULE",
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
        serial_number="SN-RULE-AF",
        operating_hours=Decimal("51"),
        cycle_count=11,
        status=ComponentStatus.INSTALLED,
    )
    dues = MaintenanceDueService.recalculate(uav)
    return {"uav": uav, "due": dues[0]}


@pytest.mark.django_db
def test_manager_can_read_and_update_due_rules(rbac, catalog):
    client = _auth_client(_user("mgr-rules@test.local", "MAINTENANCE_MANAGER"))
    listed = client.get("/api/v1/maintenance-rules/")
    assert listed.status_code == 200
    assert listed.json()["data"]["due_percent"] == 100
    assert listed.json()["data"]["auto_create_on_due"] is False

    updated = client.patch(
        "/api/v1/maintenance-rules/",
        {
            "approaching_percent": 80,
            "due_percent": 200,
            "overdue_percent": 210,
            "critical_percent": 230,
            "auto_create_on_due": False,
        },
        format="json",
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["due_percent"] == 200
    due = MaintenanceDue.objects.get(pk=catalog["due"].id)
    assert due.status == DueStatus.APPROACHING


@pytest.mark.django_db
def test_invalid_due_rule_order_rejected(rbac):
    client = _auth_client(_user("mgr-bad-rules@test.local", "MAINTENANCE_MANAGER"))
    response = client.patch(
        "/api/v1/maintenance-rules/",
        {
            "approaching_percent": 120,
            "due_percent": 100,
            "overdue_percent": 110,
            "critical_percent": 130,
            "auto_create_on_due": False,
        },
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_DUE_RULES"


@pytest.mark.django_db
def test_viewer_cannot_update_due_rules(rbac):
    client = _auth_client(_user("viewer-rules@test.local", "VIEWER"))
    response = client.patch(
        "/api/v1/maintenance-rules/",
        {
            "approaching_percent": 80,
            "due_percent": 100,
            "overdue_percent": 110,
            "critical_percent": 130,
            "auto_create_on_due": True,
        },
        format="json",
    )
    assert response.status_code == 403
