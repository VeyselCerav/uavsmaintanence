import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.audit.models import AuditLog
from apps.core.models import SystemSetting


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
        is_staff=role_code == "ADMIN",
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
def test_admin_creates_user_manager_forbidden(rbac):
    admin = _auth_client(_user("admin-usr@test.local", "ADMIN"))
    roles = admin.get("/api/v1/roles/")
    assert roles.status_code == 200
    viewer_id = next(item["id"] for item in roles.json()["data"] if item["code"] == "VIEWER")
    created = admin.post(
        "/api/v1/users/",
        {
            "email": "new-user@test.local",
            "full_name": "New User",
            "password": "secret12345",
            "role": viewer_id,
            "locale": "tr",
        },
        format="json",
    )
    assert created.status_code == 201
    assert created.json()["data"]["role_code"] == "VIEWER"

    manager = _auth_client(_user("mgr-usr@test.local", "MAINTENANCE_MANAGER"))
    forbidden = manager.get("/api/v1/users/")
    assert forbidden.status_code == 403


@pytest.mark.django_db
def test_last_admin_cannot_deactivate(rbac):
    admin_user = _user("solo-admin@test.local", "ADMIN")
    client = _auth_client(admin_user)
    response = client.patch(
        f"/api/v1/users/{admin_user.id}/",
        {"is_active": False},
        format="json",
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "LAST_ADMIN_REQUIRED"


@pytest.mark.django_db
def test_admin_updates_rpn_and_writes_audit(rbac):
    client = _auth_client(_user("admin-set@test.local", "ADMIN"))
    SystemSetting.objects.update_or_create(
        key="rpn.thresholds",
        defaults={"value": {"low_max": 49, "medium_max": 99, "high_max": 199}},
    )
    updated = client.patch(
        "/api/v1/settings/",
        {
            "key": "rpn.thresholds",
            "value": {"low_max": 40, "medium_max": 90, "high_max": 180},
        },
        format="json",
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["value"]["low_max"] == 40
    assert AuditLog.objects.filter(entity_type="SystemSetting").exists()


@pytest.mark.django_db
def test_invalid_rpn_thresholds(rbac):
    client = _auth_client(_user("admin-bad@test.local", "ADMIN"))
    response = client.patch(
        "/api/v1/settings/",
        {
            "key": "rpn.thresholds",
            "value": {"low_max": 90, "medium_max": 40, "high_max": 10},
        },
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_SETTING_VALUE"


@pytest.mark.django_db
def test_viewer_cannot_read_audit(rbac):
    client = _auth_client(_user("viewer-aud@test.local", "VIEWER"))
    response = client.get("/api/v1/audit/")
    assert response.status_code == 403
