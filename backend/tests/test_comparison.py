from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.components.models import ComponentType
from apps.failures.enums import FailureSeverity
from apps.failures.models import Failure
from apps.maintenance.enums import IntervalUnit, Priority
from apps.maintenance.models import MaintenanceTemplate, MaintenanceTemplateItem
from apps.uavs.enums import MaintenanceApproach
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
def fleet(db):
    uav_class = UAVClass.objects.create(code="MEDIUM", name="Medium")
    platform = PlatformType.objects.create(code="FIXED_WING", name="Fixed Wing")
    mission = MissionType.objects.create(code="MAPPING", name="Mapping")
    propulsion = ComponentType.objects.create(code="PROPULSION", name="Propulsion")
    cs_template = MaintenanceTemplate.objects.create(
        code="TPL-CS",
        name="Class specific",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        approach=MaintenanceApproach.CLASS_SPECIFIC,
    )
    st_template = MaintenanceTemplate.objects.create(
        code="TPL-ST",
        name="Standard",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        approach=MaintenanceApproach.STANDARD,
    )
    for template, count in ((cs_template, 2), (st_template, 1)):
        for index in range(count):
            MaintenanceTemplateItem.objects.create(
                template=template,
                component_type=propulsion,
                sequence=index + 1,
                task_code=f"{template.code}-{index}",
                task_name=f"Task {index}",
                interval_value=Decimal("50"),
                interval_unit=IntervalUnit.FLIGHT_HOURS,
                priority=Priority.MEDIUM,
            )
    cs_uav = UAV.objects.create(
        registration_number="TR-CMP-CS",
        serial_number="SN-CMP-CS",
        manufacturer="TestCo",
        model="T-CS",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        maintenance_template=cs_template,
        maintenance_approach=MaintenanceApproach.CLASS_SPECIFIC,
        total_flight_hours=Decimal("100.00"),
    )
    st_uav = UAV.objects.create(
        registration_number="TR-CMP-ST",
        serial_number="SN-CMP-ST",
        manufacturer="TestCo",
        model="T-ST",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        maintenance_template=st_template,
        maintenance_approach=MaintenanceApproach.STANDARD,
        total_flight_hours=Decimal("100.00"),
    )
    Failure.objects.create(
        uav=cs_uav,
        occurred_at=cs_uav.created_at,
        severity=FailureSeverity.HIGH,
        description="Comparison failure",
        downtime_hours=Decimal("10.00"),
        resolved_at=cs_uav.created_at,
    )
    return {
        "class": uav_class,
        "cs": cs_uav,
        "st": st_uav,
    }


def _arm(payload: dict, approach: str) -> dict:
    return next(item for item in payload["arms"] if item["approach"] == approach)


@pytest.mark.django_db
def test_comparison_groups_by_approach(rbac, fleet):
    client = _auth_client(_user("mgr-cmp@test.local", "MAINTENANCE_MANAGER"))
    response = client.get("/api/v1/reports/comparison/")
    assert response.status_code == 200
    data = response.json()["data"]
    standard = _arm(data, "STANDARD")
    specific = _arm(data, "CLASS_SPECIFIC")
    assert standard["uav_count"] == 1
    assert specific["uav_count"] == 1
    assert standard["template_item_count"] == 1
    assert specific["template_item_count"] == 2
    assert specific["failure_count"] == 1
    assert specific["mtbf_hours"] == "100.00"
    assert specific["mttr_hours"] == "10.00"
    assert specific["availability"] == "0.9091"
    assert standard["failure_count"] == 0
    assert standard["mtbf_hours"] is None


@pytest.mark.django_db
def test_comparison_filter_by_class(rbac, fleet):
    client = _auth_client(_user("mgr-flt@test.local", "MAINTENANCE_MANAGER"))
    other_class = UAVClass.objects.create(code="LIGHT", name="Light")
    response = client.get(f"/api/v1/reports/comparison/?class={other_class.id}")
    data = response.json()["data"]
    assert _arm(data, "STANDARD")["uav_count"] == 0
    assert _arm(data, "CLASS_SPECIFIC")["uav_count"] == 0


@pytest.mark.django_db
def test_viewer_can_read_technician_cannot(rbac, fleet):
    viewer = _auth_client(_user("view-cmp@test.local", "VIEWER"))
    assert viewer.get("/api/v1/reports/comparison/").status_code == 200
    tech = _auth_client(_user("tech-cmp@test.local", "TECHNICIAN"))
    assert tech.get("/api/v1/reports/comparison/").status_code == 403


@pytest.mark.django_db
def test_comparison_pdf_and_xlsx(rbac, fleet):
    client = _auth_client(_user("mgr-pdf@test.local", "MAINTENANCE_MANAGER"))
    pdf = client.get("/api/v1/reports/pdf/approach-comparison/")
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"
    xlsx = client.get("/api/v1/reports/xlsx/approach-comparison/")
    assert xlsx.status_code == 200
    assert xlsx.content[:2] == b"PK"
