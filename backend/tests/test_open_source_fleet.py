import pytest
from django.core.management import call_command

from apps.uavs.models import UAV


@pytest.mark.django_db
def test_seed_fleet_replaces_mock_with_open_source_catalog():
    call_command("seed_rbac")
    call_command("seed_dev_user")
    call_command("seed_fleet")
    assert UAV.objects.filter(registration_number="TR-UAV-001").count() == 0
    assert UAV.objects.filter(registration_number="TR-PUB-007", model="Matrice 350 RTK").exists()
    assert UAV.objects.filter(registration_number="TR-PUB-011", model="Bayraktar TB2").exists()
    assert UAV.objects.filter(registration_number="TR-PUB-004", maintenance_approach="STANDARD").exists()
    assert UAV.objects.count() == 11
