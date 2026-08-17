import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.uavs.models import MissionType, PlatformType, UAVClass


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
    return uav_class, platform, mission


@pytest.mark.django_db
def test_create_uav_binds_class_specific_template(rbac, catalog):
    uav_class, platform, mission = catalog
    from apps.maintenance.models import MaintenanceTemplate

    template = MaintenanceTemplate.objects.create(
        code="TPL-TEST",
        name="Test template",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        approach="CLASS_SPECIFIC",
        is_demo=True,
    )
    client = _auth_client(_user("manager@test.local", "MAINTENANCE_MANAGER"))
    response = client.post(
        "/api/v1/uavs/",
        {
            "registration_number": "TR-TEST-001",
            "serial_number": "SN-TEST-001",
            "manufacturer": "TestCo",
            "model": "T-1",
            "uav_class": str(uav_class.id),
            "platform_type": str(platform.id),
            "mission_type": str(mission.id),
            "maintenance_approach": "CLASS_SPECIFIC",
        },
        format="json",
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["maintenance_template"] == str(template.id)
    assert payload["data"]["template_code"] == "TPL-TEST"


@pytest.mark.django_db
def test_create_uav_without_template_returns_409(rbac, catalog):
    uav_class, platform, mission = catalog
    client = _auth_client(_user("manager2@test.local", "MAINTENANCE_MANAGER"))
    response = client.post(
        "/api/v1/uavs/",
        {
            "registration_number": "TR-TEST-002",
            "serial_number": "SN-TEST-002",
            "manufacturer": "TestCo",
            "model": "T-2",
            "uav_class": str(uav_class.id),
            "platform_type": str(platform.id),
            "mission_type": str(mission.id),
            "maintenance_approach": "CLASS_SPECIFIC",
        },
        format="json",
    )
    assert response.status_code == 409
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "MAINTENANCE_TEMPLATE_NOT_FOUND"


@pytest.mark.django_db
def test_viewer_cannot_create_uav(rbac, catalog):
    uav_class, platform, mission = catalog
    client = _auth_client(_user("viewer@test.local", "VIEWER"))
    response = client.post(
        "/api/v1/uavs/",
        {
            "registration_number": "TR-TEST-003",
            "serial_number": "SN-TEST-003",
            "manufacturer": "TestCo",
            "model": "T-3",
            "uav_class": str(uav_class.id),
            "platform_type": str(platform.id),
            "mission_type": str(mission.id),
            "maintenance_approach": "CLASS_SPECIFIC",
        },
        format="json",
    )
    assert response.status_code == 403
