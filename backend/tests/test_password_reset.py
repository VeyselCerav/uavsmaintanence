from datetime import timedelta

import pytest
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import PasswordResetToken, Role, User
from apps.accounts.services import AuthService


@pytest.fixture
def rbac(db):
    call_command("seed_rbac")


def _user(email: str, role_code: str = "ADMIN", password: str = "secret12345") -> User:
    role = Role.objects.get(code=role_code)
    return User.objects.create_user(
        email=email,
        password=password,
        full_name=role_code,
        role=role,
        is_active=True,
    )


def _client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_forgot_password_unknown_email_does_not_leak(rbac):
    response = _client().post(
        "/api/v1/auth/forgot-password/",
        {"email": "missing@local.test"},
        format="json",
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["accepted"] is True
    assert "reset_token" not in data


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_forgot_password_reset_flow(rbac):
    user = _user("reset@local.test")
    request_response = _client().post(
        "/api/v1/auth/forgot-password/",
        {"email": user.email},
        format="json",
    )
    assert request_response.status_code == 200
    token = request_response.json()["data"]["reset_token"]
    confirm = _client().post(
        "/api/v1/auth/forgot-password/confirm/",
        {"token": token, "new_password": "NewSecret12345"},
        format="json",
    )
    assert confirm.status_code == 200
    login = _client().post(
        "/api/v1/auth/login/",
        {"email": user.email, "password": "NewSecret12345"},
        format="json",
    )
    assert login.status_code == 200
    reused = _client().post(
        "/api/v1/auth/forgot-password/confirm/",
        {"token": token, "new_password": "AnotherSecret123"},
        format="json",
    )
    assert reused.status_code == 400
    assert reused.json()["error"]["code"] == "INVALID_RESET_TOKEN"


@pytest.mark.django_db
def test_expired_reset_token_rejected(rbac):
    user = _user("expired@local.test")
    raw = "expired-token-value"
    PasswordResetToken.objects.create(
        user=user,
        token_hash=AuthService._hash_token(raw),
        expires_at=timezone.now() - timedelta(minutes=1),
    )
    response = _client().post(
        "/api/v1/auth/forgot-password/confirm/",
        {"token": raw, "new_password": "NewSecret12345"},
        format="json",
    )
    assert response.status_code == 400
