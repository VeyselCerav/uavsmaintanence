from django.test import Client


def test_healthcheck():
    client = Client()
    response = client.get("/health/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"


def test_healthcheck_db():
    client = Client()
    response = client.get("/health/?db=1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready"


def test_readiness():
    client = Client()
    response = client.get("/health/ready/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready"
