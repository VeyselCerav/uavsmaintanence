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
        registration_number="TR-RPT-001",
        serial_number="SN-RPT-001",
        manufacturer="TestCo",
        model="T-RPT",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        is_demo=True,
    )
    return {"uav": uav}


@pytest.mark.django_db
def test_manager_downloads_pdf_and_xlsx(rbac, catalog):
    client = _auth_client(_user("mgr-rpt@test.local", "MAINTENANCE_MANAGER"))
    catalog_response = client.get("/api/v1/reports/")
    assert catalog_response.status_code == 200
    assert "fleet" in catalog_response.json()["data"]["pdf"]

    pdf = client.get("/api/v1/reports/pdf/fleet/")
    assert pdf.status_code == 200
    assert pdf["Content-Type"] == "application/pdf"
    assert pdf.content[:4] == b"%PDF"

    xlsx = client.get("/api/v1/reports/xlsx/uavs/")
    assert xlsx.status_code == 200
    assert xlsx.content[:2] == b"PK"


@pytest.mark.django_db
def test_uav_history_requires_uav(rbac):
    client = _auth_client(_user("mgr-hist@test.local", "MAINTENANCE_MANAGER"))
    response = client.get("/api/v1/reports/pdf/uav-history/")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "REPORT_UAV_REQUIRED"


@pytest.mark.django_db
def test_invalid_report_type(rbac):
    client = _auth_client(_user("mgr-bad@test.local", "MAINTENANCE_MANAGER"))
    response = client.get("/api/v1/reports/pdf/unknown/")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REPORT_TYPE"


@pytest.mark.django_db
def test_viewer_cannot_export(rbac):
    client = _auth_client(_user("viewer-rpt@test.local", "VIEWER"))
    listed = client.get("/api/v1/reports/")
    assert listed.status_code == 200
    exported = client.get("/api/v1/reports/pdf/fleet/")
    assert exported.status_code == 403
