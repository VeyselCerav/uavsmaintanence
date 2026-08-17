from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.components.enums import ComponentStatus
from apps.components.models import ComponentType, UAVComponent
from apps.maintenance.enums import DueStatus, InspectionType, IntervalUnit, Priority
from apps.maintenance.models import MaintenanceDue, MaintenanceTemplate, MaintenanceTemplateItem
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
        code="TPL-FLIGHT",
        name="Flight test template",
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
        priority=Priority.MEDIUM,
        inspection_type=InspectionType.VISUAL,
    )
    uav = UAV.objects.create(
        registration_number="TR-FLT-001",
        serial_number="SN-FLT-001",
        manufacturer="TestCo",
        model="T-F",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        maintenance_template=template,
        maintenance_approach="CLASS_SPECIFIC",
        total_flight_hours=Decimal("45"),
        total_flight_count=10,
        total_flight_cycles=10,
    )
    UAVComponent.objects.create(
        uav=uav,
        component_type=airframe,
        name="Airframe",
        serial_number="SN-FLT-AF",
        operating_hours=Decimal("45"),
        cycle_count=10,
        status=ComponentStatus.INSTALLED,
    )
    return {"uav": uav, "mission": mission}


@pytest.mark.django_db
def test_complete_flight_increments_counters_and_due(rbac, catalog):
    client = _auth_client(_user("op@test.local", "OPERATOR"))
    start = timezone.now() - timedelta(hours=6)
    end = timezone.now()
    created = client.post(
        "/api/v1/flights/",
        {
            "uav": str(catalog["uav"].id),
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "duration_hours": "6.00",
        },
        format="json",
    )
    assert created.status_code == 201
    flight_id = created.json()["data"]["id"]
    assert created.json()["data"]["counters_applied"] is False

    completed = client.post(f"/api/v1/flights/{flight_id}/complete/", format="json")
    assert completed.status_code == 200
    assert completed.json()["data"]["counters_applied"] is True

    catalog["uav"].refresh_from_db()
    assert catalog["uav"].total_flight_hours == Decimal("51.00")
    assert catalog["uav"].total_flight_count == 11
    assert catalog["uav"].total_flight_cycles == 11

    due = MaintenanceDue.objects.get(uav=catalog["uav"])
    assert due.status == DueStatus.DUE
    assert due.usage_percent == Decimal("102.00")

    second = client.post(f"/api/v1/flights/{flight_id}/complete/", format="json")
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "FLIGHT_COUNTERS_ALREADY_APPLIED"


@pytest.mark.django_db
def test_viewer_cannot_create_flight(rbac, catalog):
    client = _auth_client(_user("viewer-flt@test.local", "VIEWER"))
    start = timezone.now()
    response = client.post(
        "/api/v1/flights/",
        {
            "uav": str(catalog["uav"].id),
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=1)).isoformat(),
        },
        format="json",
    )
    assert response.status_code == 403
