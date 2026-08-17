from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.failures.models import Failure, FailureMode
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
    uav = UAV.objects.create(
        registration_number="TR-FAIL-001",
        serial_number="SN-FAIL-001",
        manufacturer="TestCo",
        model="T-F",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        maintenance_approach="CLASS_SPECIFIC",
    )
    mode = FailureMode.objects.create(code="PROP-IMBAL", name="Propeller imbalance")
    return {"uav": uav, "mode": mode}


@pytest.mark.django_db
def test_manager_creates_and_lists_failures(rbac, catalog):
    client = _auth_client(_user("mgr-fail@test.local", "MAINTENANCE_MANAGER"))
    occurred = timezone.now() - timedelta(hours=3)
    created = client.post(
        "/api/v1/failures/",
        {
            "uav": str(catalog["uav"].id),
            "failure_mode": str(catalog["mode"].id),
            "occurred_at": occurred.isoformat(),
            "discovered_during": "MAINTENANCE",
            "severity": "HIGH",
            "description": "Pervane titreşimi",
            "downtime_hours": "1.50",
        },
        format="json",
    )
    assert created.status_code == 201
    data = created.json()["data"]
    assert data["uav_registration"] == "TR-FAIL-001"
    assert data["failure_mode_code"] == "PROP-IMBAL"
    assert data["severity"] == "HIGH"
    assert data["resolved_at"] is None
    assert Failure.objects.filter(uav=catalog["uav"]).exists()

    listed = client.get("/api/v1/failures/?search=titreşim")
    assert listed.status_code == 200
    assert listed.json()["meta"]["total"] == 1

    open_list = client.get("/api/v1/failures/?status=open")
    assert open_list.json()["meta"]["total"] == 1


@pytest.mark.django_db
def test_viewer_cannot_create_failure(rbac, catalog):
    client = _auth_client(_user("viewer-fail@test.local", "VIEWER"))
    response = client.post(
        "/api/v1/failures/",
        {
            "uav": str(catalog["uav"].id),
            "description": "should fail",
            "discovered_during": "OTHER",
            "severity": "LOW",
        },
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_invalid_resolved_before_occurred(rbac, catalog):
    client = _auth_client(_user("mgr-fail-dates@test.local", "MAINTENANCE_MANAGER"))
    occurred = timezone.now()
    response = client.post(
        "/api/v1/failures/",
        {
            "uav": str(catalog["uav"].id),
            "occurred_at": occurred.isoformat(),
            "resolved_at": (occurred - timedelta(hours=1)).isoformat(),
            "discovered_during": "FLIGHT",
            "severity": "MEDIUM",
            "description": "tarih hatası",
        },
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FAILURE_DATES"


@pytest.mark.django_db
def test_failure_mode_code_unique_and_resolve(rbac, catalog):
    client = _auth_client(_user("mgr-mode@test.local", "MAINTENANCE_MANAGER"))
    first = client.post(
        "/api/v1/failure-modes/",
        {"code": "BATT-DEG", "name": "Battery degradation"},
        format="json",
    )
    assert first.status_code == 201
    duplicate = client.post(
        "/api/v1/failure-modes/",
        {"code": "BATT-DEG", "name": "Again"},
        format="json",
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "FAILURE_MODE_CODE_TAKEN"

    created = client.post(
        "/api/v1/failures/",
        {
            "uav": str(catalog["uav"].id),
            "description": "açık arıza",
            "discovered_during": "INSPECTION",
            "severity": "CRITICAL",
        },
        format="json",
    )
    failure_id = created.json()["data"]["id"]
    resolved = client.post(f"/api/v1/failures/{failure_id}/resolve/", format="json")
    assert resolved.status_code == 200
    assert resolved.json()["data"]["resolved_at"] is not None
    closed = client.get("/api/v1/failures/?status=resolved")
    assert closed.json()["meta"]["total"] == 1
    assert Decimal(str(created.json()["data"]["downtime_hours"])) == Decimal("0.00")
