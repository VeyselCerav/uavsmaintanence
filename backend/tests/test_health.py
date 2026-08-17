from django.test import Client


def test_healthcheck():
    client = Client()
    response = client.get("/health/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"
