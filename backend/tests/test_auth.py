import pytest
from django.test import Client

from apps.accounts.models import Role, User


@pytest.mark.django_db
def test_login_returns_tokens():
    role = Role.objects.create(code="ADMIN", name="Administrator", is_system=True)
    user = User.objects.create_user(
        email="pilot@local.test",
        password="secret12345",
        full_name="Test Pilot",
        role=role,
    )
    client = Client()
    response = client.post(
        "/api/v1/auth/login/",
        data={"email": user.email, "password": "secret12345"},
        content_type="application/json",
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "access" in payload["data"]
    assert payload["data"]["user"]["role"] == "ADMIN"


@pytest.mark.django_db
def test_login_succeeds_with_stale_authorization_header():
    role = Role.objects.create(code="ADMIN", name="Administrator", is_system=True)
    user = User.objects.create_user(
        email="stale@local.test",
        password="secret12345",
        full_name="Stale Token",
        role=role,
    )
    client = Client()
    response = client.post(
        "/api/v1/auth/login/",
        data={"email": user.email, "password": "secret12345"},
        content_type="application/json",
        HTTP_AUTHORIZATION="Bearer not-a-valid-token",
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "access" in response.json()["data"]
