from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.components.enums import ComponentStatus
from apps.components.models import ComponentType, UAVComponent
from apps.maintenance.enums import DueStatus, InspectionType, IntervalUnit, Priority
from apps.maintenance.models import MaintenanceTemplate, MaintenanceTemplateItem
from apps.maintenance.services import MaintenanceDueService
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
    airframe = ComponentType.objects.create(code="AIRFRAME", name="Airframe")
    template = MaintenanceTemplate.objects.create(
        code="TPL-TEST-DUE",
        name="Due test template",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        approach="CLASS_SPECIFIC",
        is_demo=True,
    )
    item = MaintenanceTemplateItem.objects.create(
        template=template,
        component_type=airframe,
        sequence=1,
        task_code="AF-VIS-050",
        task_name="Airframe visual",
        interval_value=Decimal("50"),
        interval_unit=IntervalUnit.FLIGHT_HOURS,
        priority=Priority.MEDIUM,
        inspection_type=InspectionType.VISUAL,
        is_demo=True,
    )
    return {
        "class": uav_class,
        "platform": platform,
        "mission": mission,
        "airframe": airframe,
        "template": template,
        "item": item,
    }


def _uav(catalog, hours=Decimal("0"), cycles=0):
    return UAV.objects.create(
        registration_number="TR-DUE-001",
        serial_number="SN-DUE-001",
        manufacturer="TestCo",
        model="T-Due",
        uav_class=catalog["class"],
        platform_type=catalog["platform"],
        mission_type=catalog["mission"],
        maintenance_template=catalog["template"],
        maintenance_approach="CLASS_SPECIFIC",
        total_flight_hours=hours,
        total_flight_cycles=cycles,
    )


def _component(uav, catalog, hours=Decimal("0"), cycles=0, installed_at=None):
    return UAVComponent.objects.create(
        uav=uav,
        component_type=catalog["airframe"],
        name="Airframe",
        serial_number="SN-AF-001",
        operating_hours=hours,
        cycle_count=cycles,
        status=ComponentStatus.INSTALLED,
        installed_at=installed_at,
        is_demo=True,
    )


@pytest.mark.django_db
def test_due_status_percent_bands(catalog):
    uav = _uav(catalog)
    _component(uav, catalog, hours=Decimal("45"))
    dues = MaintenanceDueService.recalculate(uav)
    assert len(dues) == 1
    assert dues[0].status == DueStatus.APPROACHING
    assert dues[0].usage_percent == Decimal("90.00")


@pytest.mark.django_db
def test_no_component_means_no_due(catalog):
    uav = _uav(catalog, hours=Decimal("45"))
    dues = MaintenanceDueService.recalculate(uav)
    assert dues == []


@pytest.mark.django_db
def test_calendar_due_at_interval(catalog):
    catalog["item"].interval_unit = IntervalUnit.CALENDAR_DAYS
    catalog["item"].interval_value = Decimal("90")
    catalog["item"].save()
    installed = timezone.now() - timedelta(days=90)
    uav = _uav(catalog)
    _component(uav, catalog, installed_at=installed)
    dues = MaintenanceDueService.recalculate(uav)
    assert dues[0].status == DueStatus.DUE
    assert dues[0].due_at is not None


@pytest.mark.django_db
def test_template_item_crud_and_recalculate(rbac, catalog):
    uav = _uav(catalog)
    _component(uav, catalog, hours=Decimal("10"))
    MaintenanceDueService.recalculate(uav)
    client = _auth_client(_user("mgr-due@test.local", "MAINTENANCE_MANAGER"))
    template_id = catalog["template"].id
    response = client.post(
        f"/api/v1/maintenance-templates/{template_id}/items/",
        {
            "component_type": str(catalog["airframe"].id),
            "task_code": "AF-OH-200",
            "task_name": "Overhaul",
            "interval_value": "200",
            "interval_unit": IntervalUnit.FLIGHT_HOURS,
            "priority": Priority.HIGH,
            "inspection_type": InspectionType.OVERHAUL,
        },
        format="json",
    )
    assert response.status_code == 201
    dues = client.get(f"/api/v1/maintenance-dues/?uav={uav.id}")
    assert dues.status_code == 200
    assert len(dues.json()["data"]) == 2


@pytest.mark.django_db
def test_due_list_search_and_attention_filter(rbac, catalog):
    uav = _uav(catalog)
    _component(uav, catalog, hours=Decimal("45"))
    MaintenanceDueService.recalculate(uav)
    client = _auth_client(_user("mgr-due-list@test.local", "MAINTENANCE_MANAGER"))

    rows = client.get("/api/v1/maintenance-dues/")
    assert rows.status_code == 200
    assert len(rows.json()["data"]) == 1
    assert rows.json()["data"][0]["status"] == DueStatus.APPROACHING

    attention = client.get("/api/v1/maintenance-dues/?status=attention")
    assert attention.status_code == 200
    assert len(attention.json()["data"]) == 1

    normal = client.get("/api/v1/maintenance-dues/?status=NORMAL")
    assert normal.status_code == 200
    assert len(normal.json()["data"]) == 0

    found = client.get("/api/v1/maintenance-dues/?search=TR-DUE")
    assert len(found.json()["data"]) == 1
    missed = client.get("/api/v1/maintenance-dues/?search=NOPE")
    assert len(missed.json()["data"]) == 0


@pytest.mark.django_db
def test_due_list_filters_calendar_range(rbac, catalog):
    catalog["item"].interval_unit = IntervalUnit.CALENDAR_DAYS
    catalog["item"].interval_value = Decimal("90")
    catalog["item"].save()
    installed = timezone.now() - timedelta(days=90)
    uav = _uav(catalog)
    _component(uav, catalog, installed_at=installed)
    dues = MaintenanceDueService.recalculate(uav)
    due_at = dues[0].due_at
    assert due_at is not None
    day = timezone.localtime(due_at).date().isoformat()
    client = _auth_client(_user("mgr-cal@test.local", "MAINTENANCE_MANAGER"))

    inside = client.get(f"/api/v1/maintenance-dues/?due_from={day}&due_to={day}")
    assert inside.status_code == 200
    assert len(inside.json()["data"]) == 1
    assert inside.json()["data"][0]["due_at"] is not None

    outside = client.get("/api/v1/maintenance-dues/?due_from=1999-01-01&due_to=1999-01-02")
    assert outside.status_code == 200
    assert len(outside.json()["data"]) == 0


@pytest.mark.django_db
def test_viewer_cannot_create_template_item(rbac, catalog):
    client = _auth_client(_user("viewer-due@test.local", "VIEWER"))
    response = client.post(
        f"/api/v1/maintenance-templates/{catalog['template'].id}/items/",
        {
            "component_type": str(catalog["airframe"].id),
            "task_code": "AF-X",
            "task_name": "X",
            "interval_value": "10",
            "interval_unit": IntervalUnit.FLIGHT_HOURS,
        },
        format="json",
    )
    assert response.status_code == 403
