from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.components.enums import ComponentStatus
from apps.components.models import ComponentType, UAVComponent
from apps.maintenance.enums import InspectionType, IntervalUnit, Priority
from apps.maintenance.models import MaintenanceDue, MaintenanceTemplate, MaintenanceTemplateItem
from apps.maintenance.services import MaintenanceDueService
from apps.notifications.enums import NotificationType
from apps.notifications.models import Notification
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
        code="TPL-NOTIF",
        name="Notif test template",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        approach="CLASS_SPECIFIC",
    )
    MaintenanceTemplateItem.objects.create(
        template=template,
        component_type=airframe,
        sequence=1,
        task_code="AF-VIS-050",
        task_name="Airframe visual",
        interval_value=Decimal("50"),
        interval_unit=IntervalUnit.FLIGHT_HOURS,
        priority=Priority.HIGH,
        inspection_type=InspectionType.VISUAL,
    )
    uav = UAV.objects.create(
        registration_number="TR-NOTIF-001",
        serial_number="SN-NOTIF-001",
        manufacturer="TestCo",
        model="T-NOTIF",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        maintenance_template=template,
        maintenance_approach="CLASS_SPECIFIC",
        total_flight_hours=Decimal("30"),
        total_flight_cycles=5,
    )
    UAVComponent.objects.create(
        uav=uav,
        component_type=airframe,
        name="Airframe",
        serial_number="SN-NOTIF-AF",
        operating_hours=Decimal("30"),
        cycle_count=5,
        status=ComponentStatus.INSTALLED,
    )
    MaintenanceDueService.recalculate(uav)
    return {"uav": uav}


@pytest.mark.django_db
def test_due_threshold_notifies_managers_once(rbac, catalog):
    manager = _user("mgr-notif@test.local", "MAINTENANCE_MANAGER")
    technician = _user("tech-notif@test.local", "TECHNICIAN")
    uav = catalog["uav"]
    component = uav.components.get()
    component.operating_hours = Decimal("51")
    component.save(update_fields=["operating_hours", "updated_at"])
    uav.total_flight_hours = Decimal("51")
    uav.save(update_fields=["total_flight_hours", "updated_at"])

    MaintenanceDueService.recalculate(uav)
    due_notes = Notification.objects.filter(user=manager, type=NotificationType.MAINTENANCE_DUE)
    assert due_notes.count() == 1
    assert Notification.objects.filter(user=technician).count() == 0

    MaintenanceDueService.recalculate(uav)
    assert due_notes.count() == 1

    due = MaintenanceDue.objects.get(uav=uav)
    assert due.status == "DUE"


@pytest.mark.django_db
def test_notification_api_read_own_only(rbac, catalog):
    manager = _user("mgr-api-notif@test.local", "MAINTENANCE_MANAGER")
    other = _user("mgr-other-notif@test.local", "MAINTENANCE_MANAGER")
    uav = catalog["uav"]
    component = uav.components.get()
    component.operating_hours = Decimal("51")
    component.save(update_fields=["operating_hours", "updated_at"])

    MaintenanceDueService.recalculate(uav)
    own = Notification.objects.get(user=manager)
    foreign = Notification.objects.get(user=other)

    client = _auth_client(manager)
    listed = client.get("/api/v1/notifications/")
    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()["data"]}
    assert str(own.id) in ids
    assert str(foreign.id) not in ids

    count = client.get("/api/v1/notifications/unread-count/")
    assert count.json()["data"]["unread"] == 1

    read = client.post(f"/api/v1/notifications/{own.id}/read/")
    assert read.status_code == 200
    assert read.json()["data"]["is_read"] is True
    assert client.get("/api/v1/notifications/unread-count/").json()["data"]["unread"] == 0
