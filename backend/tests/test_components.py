from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.components.enums import ComponentStatus
from apps.components.models import ComponentType, UAVComponent
from apps.maintenance.enums import InspectionType, IntervalUnit, Priority, WorkOrderStatus
from apps.maintenance.models import MaintenanceDue, MaintenanceTemplate, MaintenanceTemplateItem, WorkOrder
from apps.uavs.enums import UAVStatus
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
    propulsion = ComponentType.objects.create(code="PROPULSION", name="Propulsion")
    template = MaintenanceTemplate.objects.create(
        code="TPL-CMP",
        name="Component test template",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        approach="CLASS_SPECIFIC",
    )
    MaintenanceTemplateItem.objects.create(
        template=template,
        component_type=propulsion,
        sequence=1,
        task_code="PR-VIS-025",
        task_name="Propulsion visual",
        interval_value=Decimal("25"),
        interval_unit=IntervalUnit.FLIGHT_HOURS,
        priority=Priority.HIGH,
        inspection_type=InspectionType.VISUAL,
    )
    uav = UAV.objects.create(
        registration_number="TR-CMP-001",
        serial_number="SN-CMP-001",
        manufacturer="TestCo",
        model="T-CMP",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        maintenance_template=template,
    )
    return {"uav": uav, "type": propulsion}


@pytest.mark.django_db
def test_manager_installs_and_removes_component(rbac, catalog):
    client = _auth_client(_user("mgr-cmp@test.local", "MAINTENANCE_MANAGER"))
    created = client.post(
        "/api/v1/components/",
        {
            "uav": str(catalog["uav"].id),
            "component_type": str(catalog["type"].id),
            "serial_number": "ENG-001",
            "name": "Engine",
        },
        format="json",
    )
    assert created.status_code == 201
    data = created.json()["data"]
    assert data["status"] == ComponentStatus.INSTALLED
    assert data["serial_number"] == "ENG-001"
    assert MaintenanceDue.objects.filter(uav=catalog["uav"]).exists()

    listed = client.get(f"/api/v1/components/?uav={catalog['uav'].id}")
    assert listed.status_code == 200
    assert listed.json()["meta"]["total"] == 1

    duplicate = client.post(
        "/api/v1/components/",
        {
            "uav": str(catalog["uav"].id),
            "component_type": str(catalog["type"].id),
            "serial_number": "ENG-001",
        },
        format="json",
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "COMPONENT_SERIAL_TAKEN"

    removed = client.post(
        f"/api/v1/components/{data['id']}/remove/",
        {"status": "REMOVED", "notes": "Swap"},
        format="json",
    )
    assert removed.status_code == 200
    payload = removed.json()["data"]
    assert payload["status"] == ComponentStatus.REMOVED
    assert payload["removed_at"] is not None
    assert not MaintenanceDue.objects.filter(uav=catalog["uav"]).exists()

    again = client.post(f"/api/v1/components/{data['id']}/remove/", {}, format="json")
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "COMPONENT_NOT_INSTALLED"


@pytest.mark.django_db
def test_open_work_order_blocks_remove(rbac, catalog):
    client = _auth_client(_user("mgr-wo-cmp@test.local", "MAINTENANCE_MANAGER"))
    created = client.post(
        "/api/v1/components/",
        {
            "uav": str(catalog["uav"].id),
            "component_type": str(catalog["type"].id),
            "serial_number": "ENG-WO",
        },
        format="json",
    )
    component_id = created.json()["data"]["id"]
    WorkOrder.objects.create(
        number="WO-CMP-0001",
        uav=catalog["uav"],
        component=UAVComponent.objects.get(pk=component_id),
        status=WorkOrderStatus.OPEN,
    )
    response = client.post(f"/api/v1/components/{component_id}/remove/", {}, format="json")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "COMPONENT_OPEN_WORK_ORDER"


@pytest.mark.django_db
def test_viewer_cannot_install_component(rbac, catalog):
    client = _auth_client(_user("viewer-cmp@test.local", "VIEWER"))
    response = client.post(
        "/api/v1/components/",
        {
            "uav": str(catalog["uav"].id),
            "component_type": str(catalog["type"].id),
            "serial_number": "ENG-NO",
        },
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_cannot_install_on_retired_uav(rbac, catalog):
    catalog["uav"].status = UAVStatus.RETIRED
    catalog["uav"].save(update_fields=["status", "updated_at"])
    client = _auth_client(_user("mgr-ret@test.local", "MAINTENANCE_MANAGER"))
    response = client.post(
        "/api/v1/components/",
        {
            "uav": str(catalog["uav"].id),
            "component_type": str(catalog["type"].id),
            "serial_number": "ENG-RET",
        },
        format="json",
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "COMPONENT_UAV_RETIRED"
