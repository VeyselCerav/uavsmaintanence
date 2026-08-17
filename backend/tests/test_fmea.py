from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.components.enums import ComponentStatus
from apps.components.models import ComponentType, UAVComponent
from apps.failures.models import FailureMode
from apps.fmea.enums import FMEAStatus
from apps.fmea.models import FMEA
from apps.maintenance.enums import DueStatus, InspectionType, IntervalUnit, Priority
from apps.maintenance.models import MaintenanceDue, MaintenanceTemplate, MaintenanceTemplateItem
from apps.maintenance.work_order_services import WorkOrderService
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
    mode = FailureMode.objects.create(code="PROP-IMBAL", name="Propeller imbalance")
    template = MaintenanceTemplate.objects.create(
        code="TPL-FMEA",
        name="FMEA test template",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        approach="CLASS_SPECIFIC",
    )
    item = MaintenanceTemplateItem.objects.create(
        template=template,
        component_type=propulsion,
        sequence=1,
        task_code="PR-VIS-025",
        task_name="Propulsion visual",
        interval_value=Decimal("25"),
        interval_unit=IntervalUnit.FLIGHT_HOURS,
        priority=Priority.MEDIUM,
        inspection_type=InspectionType.VISUAL,
    )
    uav = UAV.objects.create(
        registration_number="TR-FMEA-001",
        serial_number="SN-FMEA-001",
        manufacturer="TestCo",
        model="T-FMEA",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        maintenance_template=template,
        maintenance_approach="CLASS_SPECIFIC",
    )
    component = UAVComponent.objects.create(
        uav=uav,
        component_type=propulsion,
        name="Propulsion",
        serial_number="SN-FMEA-PR",
        status=ComponentStatus.INSTALLED,
    )
    return {
        "class": uav_class,
        "platform": platform,
        "mission": mission,
        "propulsion": propulsion,
        "mode": mode,
        "uav": uav,
        "component": component,
        "template_item": item,
    }


@pytest.mark.django_db
def test_manager_creates_fmea_item_computes_rpn(rbac, catalog):
    client = _auth_client(_user("mgr-fmea@test.local", "MAINTENANCE_MANAGER"))
    created = client.post(
        "/api/v1/fmea/",
        {
            "code": "FMEA-TEST-001",
            "title": "Propulsion analysis",
            "uav_class": str(catalog["class"].id),
            "platform_type": str(catalog["platform"].id),
            "component_type": str(catalog["propulsion"].id),
            "mission_type": str(catalog["mission"].id),
        },
        format="json",
    )
    assert created.status_code == 201
    fmea_id = created.json()["data"]["id"]
    assert created.json()["data"]["status"] == "DRAFT"
    assert created.json()["data"]["max_rpn"] is None

    item = client.post(
        f"/api/v1/fmea/{fmea_id}/items/",
        {
            "function": "İtki üretmek",
            "functional_failure": "İtki kaybı",
            "failure_mode": "Pervane dengesizliği",
            "catalog_mode": str(catalog["mode"].id),
            "severity": 8,
            "occurrence": 5,
            "detection": 4,
        },
        format="json",
    )
    assert item.status_code == 201
    data = item.json()["data"]
    assert data["rpn"] == 160
    assert data["rpn_band"] == "HIGH"
    assert data["catalog_mode_code"] == "PROP-IMBAL"

    invalid = client.post(
        f"/api/v1/fmea/{fmea_id}/items/",
        {
            "function": "x",
            "functional_failure": "y",
            "failure_mode": "z",
            "severity": 11,
            "occurrence": 1,
            "detection": 1,
        },
        format="json",
    )
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "INVALID_FMEA_SCORES"


@pytest.mark.django_db
def test_viewer_cannot_create_fmea(rbac, catalog):
    client = _auth_client(_user("viewer-fmea@test.local", "VIEWER"))
    response = client.post(
        "/api/v1/fmea/",
        {
            "code": "FMEA-NOPE",
            "title": "Nope",
            "uav_class": str(catalog["class"].id),
            "platform_type": str(catalog["platform"].id),
            "component_type": str(catalog["propulsion"].id),
        },
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_approve_locks_edits_and_filters_by_uav(rbac, catalog):
    client = _auth_client(_user("mgr-approve@test.local", "MAINTENANCE_MANAGER"))
    created = client.post(
        "/api/v1/fmea/",
        {
            "code": "FMEA-LOCK-001",
            "title": "Lock test",
            "uav_class": str(catalog["class"].id),
            "platform_type": str(catalog["platform"].id),
            "component_type": str(catalog["propulsion"].id),
            "mission_type": str(catalog["mission"].id),
        },
        format="json",
    )
    fmea_id = created.json()["data"]["id"]
    approved = client.post(f"/api/v1/fmea/{fmea_id}/approve/", format="json")
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == "APPROVED"
    assert approved.json()["data"]["revision"] == 1

    locked = client.patch(
        f"/api/v1/fmea/{fmea_id}/",
        {"title": "changed"},
        format="json",
    )
    assert locked.status_code == 409
    assert locked.json()["error"]["code"] == "FMEA_LOCKED"

    listed = client.get(f"/api/v1/fmea/?uav={catalog['uav'].id}")
    assert listed.status_code == 200
    assert listed.json()["meta"]["total"] == 1


@pytest.mark.django_db
def test_work_order_priority_uses_approved_rpn(rbac, catalog):
    manager = _user("mgr-prio@test.local", "MAINTENANCE_MANAGER")
    fmea = FMEA.objects.create(
        code="FMEA-PRIO-001",
        title="Priority",
        uav_class=catalog["class"],
        platform_type=catalog["platform"],
        component_type=catalog["propulsion"],
        mission_type=catalog["mission"],
        status=FMEAStatus.APPROVED,
        revision=1,
    )
    from apps.fmea.models import FMEAItem

    FMEAItem.objects.create(
        fmea=fmea,
        sequence=1,
        function="Thrust",
        functional_failure="Loss",
        failure_mode="Imbalance",
        severity=8,
        occurrence=5,
        detection=5,
        rpn=200,
    )
    due = MaintenanceDue.objects.create(
        uav=catalog["uav"],
        component=catalog["component"],
        template_item=catalog["template_item"],
        status=DueStatus.OVERDUE,
        remaining_value=Decimal("-5"),
        remaining_unit=IntervalUnit.FLIGHT_HOURS,
        usage_percent=Decimal("120"),
        calculated_at=catalog["uav"].updated_at,
        priority=Priority.MEDIUM,
    )
    work_order = WorkOrderService.create_from_due(actor=manager, due=due)
    assert work_order.priority == Priority.CRITICAL
