import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import Role, User


@pytest.fixture
def rbac(db):
    call_command("seed_rbac")


def _user(email: str, role_code: str, password: str = "secret12345") -> User:
    role = Role.objects.get(code=role_code)
    return User.objects.create_user(
        email=email,
        password=password,
        full_name="Profile User",
        role=role,
        is_active=True,
        locale="tr",
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
def test_profile_updates_name_and_locale(rbac):
    user = _user("prof@test.local", "TECHNICIAN")
    client = _auth_client(user)
    response = client.patch(
        "/api/v1/auth/me/",
        {"full_name": "Yeni Ad", "locale": "en"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["data"]["full_name"] == "Yeni Ad"
    assert response.json()["data"]["locale"] == "en"
    user.refresh_from_db()
    assert user.locale == "en"


@pytest.mark.django_db
def test_profile_rejects_wrong_current_password(rbac):
    user = _user("pwd@test.local", "TECHNICIAN")
    client = _auth_client(user)
    response = client.patch(
        "/api/v1/auth/me/",
        {"current_password": "wrong-pass", "new_password": "newsecret99"},
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_CURRENT_PASSWORD"


@pytest.mark.django_db
def test_profile_changes_password(rbac):
    user = _user("pwd2@test.local", "TECHNICIAN")
    client = _auth_client(user)
    response = client.patch(
        "/api/v1/auth/me/",
        {"current_password": "secret12345", "new_password": "newsecret99"},
        format="json",
    )
    assert response.status_code == 200
    login = APIClient().post(
        "/api/v1/auth/login/",
        {"email": user.email, "password": "newsecret99"},
        format="json",
    )
    assert login.status_code == 200
