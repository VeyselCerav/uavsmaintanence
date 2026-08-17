import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.technicians.models import Technician


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
def test_manager_creates_technician_profile(rbac):
    manager = _user("mgr-tech@test.local", "MAINTENANCE_MANAGER")
    client = _auth_client(manager)
    created = client.post(
        "/api/v1/technicians/",
        {
            "employee_number": "EMP-100",
            "email": "ali.tech@test.local",
            "full_name": "Ali Teknisyen",
            "password": "secret12345",
        },
        format="json",
    )
    assert created.status_code == 201
    data = created.json()["data"]
    assert data["employee_number"] == "EMP-100"
    assert data["email"] == "ali.tech@test.local"
    assert data["role"] == "TECHNICIAN"
    assert Technician.objects.filter(employee_number="EMP-100").exists()

    duplicate = client.post(
        "/api/v1/technicians/",
        {
            "employee_number": "EMP-101",
            "email": "ali.tech@test.local",
            "full_name": "Ali 2",
            "password": "secret12345",
        },
        format="json",
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "TECHNICIAN_EMAIL_TAKEN"


@pytest.mark.django_db
def test_viewer_cannot_create_technician(rbac):
    client = _auth_client(_user("viewer-tech@test.local", "VIEWER"))
    response = client.post(
        "/api/v1/technicians/",
        {
            "employee_number": "EMP-200",
            "email": "nope@test.local",
            "full_name": "Nope",
            "password": "secret12345",
        },
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_manager_assigns_skill_and_certification(rbac):
    manager = _user("mgr-skill@test.local", "MAINTENANCE_MANAGER")
    client = _auth_client(manager)
    skill = client.post(
        "/api/v1/skills/",
        {"code": "VISUAL", "name": "Visual inspection"},
        format="json",
    )
    assert skill.status_code == 201
    skill_id = skill.json()["data"]["id"]

    duplicate_skill = client.post(
        "/api/v1/skills/",
        {"code": "VISUAL", "name": "Visual 2"},
        format="json",
    )
    assert duplicate_skill.status_code == 409
    assert duplicate_skill.json()["error"]["code"] == "SKILL_CODE_TAKEN"

    created = client.post(
        "/api/v1/technicians/",
        {
            "employee_number": "EMP-300",
            "email": "skill.tech@test.local",
            "full_name": "Skill Tech",
            "password": "secret12345",
        },
        format="json",
    )
    tech_id = created.json()["data"]["id"]
    added = client.post(
        f"/api/v1/technicians/{tech_id}/skills/",
        {"skill": skill_id, "certified_at": "2025-01-01", "expires_at": "2026-01-01"},
        format="json",
    )
    assert added.status_code == 201
    assert added.json()["data"]["skill_code"] == "VISUAL"

    again = client.post(
        f"/api/v1/technicians/{tech_id}/skills/",
        {"skill": skill_id},
        format="json",
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "TECHNICIAN_SKILL_EXISTS"

    invalid = client.post(
        f"/api/v1/technicians/{tech_id}/certifications/",
        {
            "name": "Part-66",
            "issuer": "SHGM",
            "issued_at": "2026-01-01",
            "expires_at": "2025-01-01",
        },
        format="json",
    )
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "INVALID_CERTIFICATION_DATES"

    cert = client.post(
        f"/api/v1/technicians/{tech_id}/certifications/",
        {
            "name": "Part-66 B1",
            "issuer": "SHGM",
            "issued_at": "2024-06-01",
            "expires_at": "2027-06-01",
            "document_id": "SHGM-P66-B1-001",
        },
        format="json",
    )
    assert cert.status_code == 201
    assert cert.json()["data"]["document_id"] == "SHGM-P66-B1-001"
    detail = client.get(f"/api/v1/technicians/{tech_id}/")
    assert len(detail.json()["data"]["skills"]) == 1
    assert len(detail.json()["data"]["certifications"]) == 1
    assert detail.json()["data"]["certifications"][0]["document_id"] == "SHGM-P66-B1-001"


@pytest.mark.django_db
def test_viewer_cannot_create_skill(rbac):
    client = _auth_client(_user("viewer-skill@test.local", "VIEWER"))
    response = client.post("/api/v1/skills/", {"code": "X", "name": "X"}, format="json")
    assert response.status_code == 403
