from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.components.enums import ComponentStatus
from apps.components.models import ComponentType, UAVComponent
from apps.core.models import SystemSetting
from apps.failures.enums import FailureSeverity
from apps.failures.models import Failure
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
    propulsion = ComponentType.objects.create(code="PROPULSION", name="Propulsion")
    uav = UAV.objects.create(
        registration_number="TR-REL-001",
        serial_number="SN-REL-001",
        manufacturer="TestCo",
        model="T-REL",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        total_flight_hours=Decimal("100.00"),
    )
    component = UAVComponent.objects.create(
        uav=uav,
        component_type=propulsion,
        name="Propulsion",
        serial_number="SN-REL-PR",
        operating_hours=Decimal("80.00"),
        status=ComponentStatus.INSTALLED,
    )
    return {
        "class": uav_class,
        "uav": uav,
        "component": component,
    }


def _failure(uav, component, downtime, resolved=True):
    now = timezone.now()
    return Failure.objects.create(
        uav=uav,
        component=component,
        occurred_at=now,
        severity=FailureSeverity.HIGH,
        description="Test failure",
        downtime_hours=Decimal(str(downtime)),
        resolved_at=now if resolved else None,
    )


@pytest.mark.django_db
def test_mtbf_mttr_availability_from_server(rbac, catalog):
    _failure(catalog["uav"], catalog["component"], "5.00")
    _failure(catalog["uav"], catalog["component"], "15.00")
    client = _auth_client(_user("mgr-rel@test.local", "MAINTENANCE_MANAGER"))
    response = client.get(
        f"/api/v1/reliability/?scope=uav&scope_id={catalog['uav'].id}",
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["failure_count"] == 2
    assert data["repair_count"] == 2
    assert data["mtbf_hours"] == "50.00"
    assert data["mttr_hours"] == "10.00"
    assert data["availability"] == "0.8333"
    assert data["is_lower_bound"] is False


@pytest.mark.django_db
def test_zero_failures_returns_null_mtbf(rbac, catalog):
    client = _auth_client(_user("mgr-zero@test.local", "MAINTENANCE_MANAGER"))
    response = client.get(
        f"/api/v1/reliability/?scope=uav&scope_id={catalog['uav'].id}",
    )
    data = response.json()["data"]
    assert data["failure_count"] == 0
    assert data["mtbf_hours"] is None
    assert data["availability"] is None
    assert data["zero_failure_policy"] == "undefined"


@pytest.mark.django_db
def test_zero_failure_lower_bound_policy(rbac, catalog):
    SystemSetting.objects.update_or_create(
        key="reliability.zero_failure_policy",
        defaults={"value": "operating_time_as_lower_bound"},
    )
    client = _auth_client(_user("mgr-bound@test.local", "MAINTENANCE_MANAGER"))
    response = client.get(
        f"/api/v1/reliability/?scope=uav&scope_id={catalog['uav'].id}",
    )
    data = response.json()["data"]
    assert data["mtbf_hours"] == "100.00"
    assert data["is_lower_bound"] is True
    assert data["mttr_hours"] is None
    assert data["availability"] is None


@pytest.mark.django_db
def test_component_scope_and_technician_forbidden(rbac, catalog):
    _failure(catalog["uav"], catalog["component"], "8.00")
    manager = _auth_client(_user("mgr-comp@test.local", "MAINTENANCE_MANAGER"))
    response = manager.get(
        f"/api/v1/reliability/?scope=component&scope_id={catalog['component'].id}",
    )
    assert response.status_code == 200
    assert response.json()["data"]["mtbf_hours"] == "80.00"

    technician = _auth_client(_user("tech-rel@test.local", "TECHNICIAN"))
    forbidden = technician.get("/api/v1/reliability/?scope=fleet")
    assert forbidden.status_code == 403


@pytest.mark.django_db
def test_invalid_scope_rejected(rbac, catalog):
    client = _auth_client(_user("mgr-bad@test.local", "MAINTENANCE_MANAGER"))
    response = client.get("/api/v1/reliability/?scope=planet")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "RELIABILITY_INVALID_SCOPE"
