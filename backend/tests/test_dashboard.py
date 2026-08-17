from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.components.enums import ComponentStatus
from apps.components.models import ComponentType, UAVComponent
from apps.maintenance.enums import InspectionType, IntervalUnit, Priority
from apps.maintenance.models import MaintenanceTemplate, MaintenanceTemplateItem
from apps.maintenance.services import MaintenanceDueService
from apps.technicians.models import Technician
from apps.uavs.enums import UAVStatus
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
        code="TPL-DASH",
        name="Dashboard template",
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
        registration_number="TR-DASH-001",
        serial_number="SN-DASH-001",
        manufacturer="TestCo",
        model="T-Dash",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        maintenance_template=template,
        maintenance_approach="CLASS_SPECIFIC",
        status=UAVStatus.MAINTENANCE,
        total_flight_hours=Decimal("51"),
        total_flight_cycles=11,
    )
    UAVComponent.objects.create(
        uav=uav,
        component_type=airframe,
        name="Airframe",
        serial_number="SN-DASH-AF",
        operating_hours=Decimal("51"),
        cycle_count=11,
        status=ComponentStatus.INSTALLED,
    )
    dues = MaintenanceDueService.recalculate(uav)
    return {"uav": uav, "due": dues[0]}


@pytest.mark.django_db
def test_dashboard_summary_counts_and_technician_scope(rbac, catalog):
    manager = _user("mgr-dash@test.local", "MAINTENANCE_MANAGER")
    tech_user = _user("tech-dash@test.local", "TECHNICIAN")
    technician = Technician.objects.create(user=tech_user, employee_number="EMP-DASH-1")
    manager_client = _auth_client(manager)

    created = manager_client.post(
        "/api/v1/work-orders/",
        {"due": str(catalog["due"].id)},
        format="json",
    )
    assert created.status_code == 201
    work_id = created.json()["data"]["id"]
    assigned = manager_client.post(
        f"/api/v1/work-orders/{work_id}/assign/",
        {"assigned_technician": str(technician.id)},
        format="json",
    )
    assert assigned.status_code == 200

    summary = manager_client.get("/api/v1/dashboard/")
    assert summary.status_code == 200
    data = summary.json()["data"]
    assert data["fleet"]["MAINTENANCE"] == 1
    assert data["fleet"]["total"] == 1
    assert data["dues"]["counts"]["DUE"] == 1
    assert data["dues"]["counts"]["attention"] == 1
    assert data["work_orders"]["counts"]["open"] == 1
    assert data["work_orders"]["counts"]["ASSIGNED"] == 1
    assert data["work_orders"]["counts"]["COMPLETED"] == 0
    assert data["work_orders"]["counts"]["CANCELLED"] == 0
    assert data["dues"]["counts"]["overdue"] == 0
    assert data["dues"]["overdue_items"] == []
    assert data["dues"]["items"][0]["uav_registration"] == "TR-DASH-001"
    assert data["work_orders"]["items"][0]["id"] == work_id

    tech_summary = _auth_client(tech_user).get("/api/v1/dashboard/")
    assert tech_summary.status_code == 200
    tech_data = tech_summary.json()["data"]
    assert tech_data["work_orders"]["counts"]["open"] == 1
    assert tech_data["work_orders"]["items"][0]["id"] == work_id

    other_tech = _user("tech-dash-2@test.local", "TECHNICIAN")
    other_summary = _auth_client(other_tech).get("/api/v1/dashboard/")
    assert other_summary.json()["data"]["work_orders"]["counts"]["open"] == 0
    assert other_summary.json()["data"]["work_orders"]["items"] == []


@pytest.mark.django_db
def test_unauthenticated_cannot_view_dashboard(rbac):
    response = APIClient().get("/api/v1/dashboard/")
    assert response.status_code == 401
