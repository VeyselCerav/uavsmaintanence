from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.components.models import ComponentType
from apps.maintenance.enums import InspectionType, IntervalUnit, Priority, RCMStrategy
from apps.maintenance.models import MaintenanceTemplate, MaintenanceTemplateItem
from apps.rcm.enums import Detectability
from apps.rcm.services import RCMEvaluationService
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
        code="TPL-RCM",
        name="RCM test template",
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
        rcm_strategy=RCMStrategy.SCHEDULED_INSPECTION,
    )
    uav = UAV.objects.create(
        registration_number="TR-RCM-001",
        serial_number="SN-RCM-001",
        manufacturer="TestCo",
        model="T-RCM",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
        maintenance_template=template,
        maintenance_approach="CLASS_SPECIFIC",
    )
    return {
        "class": uav_class,
        "platform": platform,
        "mission": mission,
        "propulsion": propulsion,
        "uav": uav,
        "template_item": item,
    }


def _create_analysis(client: APIClient, catalog: dict, code: str = "RCM-TEST-001"):
    created = client.post(
        "/api/v1/rcm/",
        {
            "code": code,
            "title": "Propulsion RCM",
            "uav_class": str(catalog["class"].id),
            "platform_type": str(catalog["platform"].id),
            "component_type": str(catalog["propulsion"].id),
            "mission_type": str(catalog["mission"].id),
        },
        format="json",
    )
    assert created.status_code == 201
    return created.json()["data"]


@pytest.mark.parametrize(
    ("safety", "operational", "preventive", "detectability", "expected"),
    [
        (True, False, True, Detectability.HIGH, RCMStrategy.CONDITION_INSPECTION),
        (True, False, True, Detectability.MEDIUM, RCMStrategy.SCHEDULED_RESTORATION),
        (True, False, True, Detectability.LOW, RCMStrategy.SCHEDULED_RESTORATION),
        (True, True, False, Detectability.HIGH, RCMStrategy.CORRECTIVE),
        (False, True, True, Detectability.HIGH, RCMStrategy.CONDITION_INSPECTION),
        (False, True, True, Detectability.LOW, RCMStrategy.SCHEDULED_INSPECTION),
        (False, True, False, Detectability.HIGH, RCMStrategy.CORRECTIVE),
        (False, False, True, Detectability.HIGH, RCMStrategy.FUNCTIONAL_CHECK),
        (False, False, False, Detectability.HIGH, RCMStrategy.CORRECTIVE),
    ],
)
def test_rcm_decision_tree(safety, operational, preventive, detectability, expected):
    assert (
        RCMEvaluationService.evaluate(
            safety_effect=safety,
            operational_effect=operational,
            preventive_feasible=preventive,
            detectability=detectability,
        )
        == expected
    )
    assert RCMEvaluationService.grounded_warning(
        safety_effect=safety,
        preventive_feasible=preventive,
    ) is (safety and not preventive)


@pytest.mark.django_db
def test_manager_creates_item_uses_server_tree(rbac, catalog):
    client = _auth_client(_user("mgr-rcm@test.local", "MAINTENANCE_MANAGER"))
    analysis = _create_analysis(client, catalog)
    item = client.post(
        f"/api/v1/rcm/{analysis['id']}/items/",
        {
            "function": "İtki üretmek",
            "functional_failure": "İtki kaybı",
            "failure_mode": "Pervane dengesizliği",
            "safety_effect": False,
            "operational_effect": True,
            "preventive_feasible": True,
            "detectability": Detectability.HIGH,
        },
        format="json",
    )
    assert item.status_code == 201
    data = item.json()["data"]
    assert data["suggested_strategy"] == RCMStrategy.CONDITION_INSPECTION
    assert data["strategy"] == RCMStrategy.CONDITION_INSPECTION
    assert data["is_overridden"] is False
    assert data["grounded_warning"] is False


@pytest.mark.django_db
def test_override_without_rationale_is_rejected(rbac, catalog):
    client = _auth_client(_user("mgr-override@test.local", "MAINTENANCE_MANAGER"))
    analysis = _create_analysis(client, catalog, "RCM-OVR-001")
    response = client.post(
        f"/api/v1/rcm/{analysis['id']}/items/",
        {
            "function": "İtki",
            "functional_failure": "Kayıp",
            "failure_mode": "Aşınma",
            "safety_effect": False,
            "operational_effect": True,
            "preventive_feasible": True,
            "detectability": Detectability.HIGH,
            "strategy": RCMStrategy.SCHEDULED_DISCARD,
        },
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "RCM_RATIONALE_REQUIRED"


@pytest.mark.django_db
def test_viewer_cannot_create_rcm(rbac, catalog):
    client = _auth_client(_user("viewer-rcm@test.local", "VIEWER"))
    response = client.post(
        "/api/v1/rcm/",
        {
            "code": "RCM-NOPE",
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
    client = _auth_client(_user("mgr-approve-rcm@test.local", "MAINTENANCE_MANAGER"))
    analysis = _create_analysis(client, catalog, "RCM-LOCK-001")
    approved = client.post(f"/api/v1/rcm/{analysis['id']}/approve/", format="json")
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == "APPROVED"
    assert approved.json()["data"]["revision"] == 1

    locked = client.patch(
        f"/api/v1/rcm/{analysis['id']}/",
        {"title": "changed"},
        format="json",
    )
    assert locked.status_code == 409
    assert locked.json()["error"]["code"] == "RCM_LOCKED"

    listed = client.get(f"/api/v1/rcm/?uav={catalog['uav'].id}")
    assert listed.status_code == 200
    assert listed.json()["meta"]["total"] == 1


@pytest.mark.django_db
def test_apply_to_template_copies_single_strategy(rbac, catalog):
    client = _auth_client(_user("mgr-apply@test.local", "MAINTENANCE_MANAGER"))
    analysis = _create_analysis(client, catalog, "RCM-APPLY-001")
    client.post(
        f"/api/v1/rcm/{analysis['id']}/items/",
        {
            "function": "İtki",
            "functional_failure": "Kayıp",
            "failure_mode": "Dengesizlik",
            "safety_effect": False,
            "operational_effect": True,
            "preventive_feasible": True,
            "detectability": Detectability.HIGH,
        },
        format="json",
    )
    draft_apply = client.post(
        f"/api/v1/rcm/{analysis['id']}/apply-to-template/",
        format="json",
    )
    assert draft_apply.status_code == 409
    assert draft_apply.json()["error"]["code"] == "RCM_NOT_APPROVED"

    client.post(f"/api/v1/rcm/{analysis['id']}/approve/", format="json")
    applied = client.post(
        f"/api/v1/rcm/{analysis['id']}/apply-to-template/",
        format="json",
    )
    assert applied.status_code == 200
    assert applied.json()["data"]["updated"] == 1
    assert applied.json()["data"]["strategy"] == RCMStrategy.CONDITION_INSPECTION
    catalog["template_item"].refresh_from_db()
    assert catalog["template_item"].rcm_strategy == RCMStrategy.CONDITION_INSPECTION
