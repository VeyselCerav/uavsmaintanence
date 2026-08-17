from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.documents.enums import DocumentType
from apps.documents.models import Document
from apps.flights.enums import FlightResult
from apps.flights.models import Flight
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


@pytest.mark.django_db
def test_uav_timeline_orders_events(rbac):
    uav_class = UAVClass.objects.create(code="MEDIUM", name="Medium")
    platform = PlatformType.objects.create(code="FIXED_WING", name="Fixed Wing")
    mission = MissionType.objects.create(code="MAPPING", name="Mapping")
    uav = UAV.objects.create(
        registration_number="TR-TL-001",
        serial_number="SN-TL-001",
        manufacturer="TestCo",
        model="T-TL",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
    )
    now = timezone.now()
    Flight.objects.create(
        flight_number="FL-TL-001",
        uav=uav,
        mission_type=mission,
        flown_on=now.date(),
        start_at=now - timedelta(hours=2),
        end_at=now - timedelta(hours=1),
        duration_hours=Decimal("1.00"),
        result=FlightResult.COMPLETED,
    )
    Document.objects.create(
        title="Timeline doc",
        file_name="tl.pdf",
        storage_key="DOC-TL-001",
        document_type=DocumentType.REPORT,
        uav=uav,
    )
    client = _auth_client(_user("mgr-tl@test.local", "MAINTENANCE_MANAGER"))
    response = client.get(f"/api/v1/uavs/{uav.id}/timeline/")
    assert response.status_code == 200
    types = [item["event_type"] for item in response.json()["data"]]
    assert "UAV_CREATED" in types
    assert "FLIGHT" in types
    assert "DOCUMENT" in types
    occurred = [item["occurred_at"] for item in response.json()["data"]]
    assert occurred == sorted(occurred, reverse=True)
