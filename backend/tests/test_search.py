import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
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
    token = response.json()["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def catalog(db):
    uav_class = UAVClass.objects.create(code="MEDIUM", name="Medium")
    platform = PlatformType.objects.create(code="FIXED_WING", name="Fixed Wing")
    mission = MissionType.objects.create(code="MAPPING", name="Mapping")
    UAV.objects.create(
        registration_number="TR-SRCH-001",
        serial_number="SN-SRCH-001",
        manufacturer="TestCo",
        model="T-SRCH",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
    )


@pytest.mark.django_db
def test_search_finds_uav(rbac, catalog):
    client = _auth_client(_user("mgr-srch@test.local", "MAINTENANCE_MANAGER"))
    response = client.get("/api/v1/search/?q=TR-SRCH")
    assert response.status_code == 200
    groups = response.json()["data"]["groups"]
    uav_group = next(group for group in groups if group["entity"] == "uav")
    assert uav_group["items"][0]["title"] == "TR-SRCH-001"


@pytest.mark.django_db
def test_search_short_query_empty(rbac, catalog):
    client = _auth_client(_user("mgr-short@test.local", "MAINTENANCE_MANAGER"))
    response = client.get("/api/v1/search/?q=T")
    assert response.json()["data"]["groups"] == []
