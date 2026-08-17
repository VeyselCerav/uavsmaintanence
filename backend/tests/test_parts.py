
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.components.enums import ComponentStatus
from apps.components.models import ComponentType, UAVComponent
from apps.maintenance.enums import WorkOrderStatus
from apps.maintenance.models import WorkOrder
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
    other_platform = PlatformType.objects.create(code="MULTICOPTER", name="Multicopter")
    mission = MissionType.objects.create(code="MAPPING", name="Mapping")
    propulsion = ComponentType.objects.create(code="PROPULSION", name="Propulsion")
    uav = UAV.objects.create(
        registration_number="TR-PART-001",
        serial_number="SN-PART-001",
        manufacturer="TestCo",
        model="T-PART",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
    )
    component = UAVComponent.objects.create(
        uav=uav,
        component_type=propulsion,
        name="Propulsion",
        serial_number="SN-PART-PR",
        status=ComponentStatus.INSTALLED,
    )
    work_order = WorkOrder.objects.create(
        number="WO-PART-001",
        uav=uav,
        component=component,
        status=WorkOrderStatus.OPEN,
    )
    return {
        "class": uav_class,
        "platform": platform,
        "other_platform": other_platform,
        "propulsion": propulsion,
        "uav": uav,
        "component": component,
        "work_order": work_order,
    }


def _create_part(client, catalog, number="PN-001", stock="4.00"):
    created = client.post(
        "/api/v1/parts/",
        {
            "part_number": number,
            "name": "Propeller blade",
            "stock_qty": stock,
            "min_stock_qty": "2.00",
            "unit_cost": "150.00",
            "currency": "TRY",
        },
        format="json",
    )
    assert created.status_code == 201
    part_id = created.json()["data"]["id"]
    compat = client.post(
        f"/api/v1/parts/{part_id}/compatibility/",
        {
            "uav_class": str(catalog["class"].id),
            "platform_type": str(catalog["platform"].id),
            "component_type": str(catalog["propulsion"].id),
        },
        format="json",
    )
    assert compat.status_code == 201
    return created.json()["data"]


@pytest.mark.django_db
def test_manager_creates_part_and_cost_total(rbac, catalog):
    client = _auth_client(_user("mgr-part@test.local", "MAINTENANCE_MANAGER"))
    part = _create_part(client, catalog)
    assert part["stock_low"] is False

    cost = client.post(
        "/api/v1/costs/",
        {
            "uav": str(catalog["uav"].id),
            "work_order": str(catalog["work_order"].id),
            "part_cost": "10.00",
            "labor_cost": "20.00",
            "other_cost": "5.00",
            "currency": "TRY",
        },
        format="json",
    )
    assert cost.status_code == 201
    assert cost.json()["data"]["total_cost"] == "35.00"

    listed = client.get(f"/api/v1/costs/?uav={catalog['uav'].id}")
    assert listed.status_code == 200
    assert listed.json()["meta"]["total"] == 1


@pytest.mark.django_db
def test_work_order_part_decrements_stock(rbac, catalog):
    client = _auth_client(_user("mgr-issue@test.local", "MAINTENANCE_MANAGER"))
    part = _create_part(client, catalog, "PN-ISSUE")
    issued = client.post(
        f"/api/v1/work-orders/{catalog['work_order'].id}/parts/",
        {"part": part["id"], "quantity": "1.00"},
        format="json",
    )
    assert issued.status_code == 201
    assert issued.json()["data"]["line_cost"] == "150.00"

    stored = client.get(f"/api/v1/parts/{part['id']}/")
    assert stored.json()["data"]["stock_qty"] == "3.00"

    costs = client.get(f"/api/v1/costs/?work_order={catalog['work_order'].id}")
    assert costs.json()["data"][0]["part_cost"] == "150.00"
    assert costs.json()["data"][0]["total_cost"] == "150.00"


@pytest.mark.django_db
def test_incompatible_and_insufficient_stock(rbac, catalog):
    client = _auth_client(_user("mgr-badpart@test.local", "MAINTENANCE_MANAGER"))
    created = client.post(
        "/api/v1/parts/",
        {
            "part_number": "PN-MC",
            "name": "Multicopter hub",
            "stock_qty": "1.00",
            "unit_cost": "10.00",
        },
        format="json",
    )
    part_id = created.json()["data"]["id"]
    client.post(
        f"/api/v1/parts/{part_id}/compatibility/",
        {
            "uav_class": str(catalog["class"].id),
            "platform_type": str(catalog["other_platform"].id),
            "component_type": str(catalog["propulsion"].id),
        },
        format="json",
    )
    incompatible = client.post(
        f"/api/v1/work-orders/{catalog['work_order'].id}/parts/",
        {"part": part_id, "quantity": "1.00"},
        format="json",
    )
    assert incompatible.status_code == 409
    assert incompatible.json()["error"]["code"] == "PART_INCOMPATIBLE"

    matching = _create_part(client, catalog, "PN-LOW", stock="1.00")
    short = client.post(
        f"/api/v1/work-orders/{catalog['work_order'].id}/parts/",
        {"part": matching["id"], "quantity": "5.00"},
        format="json",
    )
    assert short.status_code == 409
    assert short.json()["error"]["code"] == "INSUFFICIENT_STOCK"


@pytest.mark.django_db
def test_viewer_cannot_create_part(rbac, catalog):
    client = _auth_client(_user("viewer-part@test.local", "VIEWER"))
    response = client.post(
        "/api/v1/parts/",
        {"part_number": "PN-NOPE", "name": "Nope"},
        format="json",
    )
    assert response.status_code == 403
