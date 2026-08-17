import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
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
def uav(db):
    uav_class = UAVClass.objects.create(code="MEDIUM", name="Medium")
    platform = PlatformType.objects.create(code="FIXED_WING", name="Fixed Wing")
    mission = MissionType.objects.create(code="MAPPING", name="Mapping")
    return UAV.objects.create(
        registration_number="TR-DOC-001",
        serial_number="SN-DOC-001",
        manufacturer="TestCo",
        model="T-DOC",
        uav_class=uav_class,
        platform_type=platform,
        mission_type=mission,
    )


@pytest.mark.django_db
def test_manager_creates_document(rbac, uav):
    client = _auth_client(_user("mgr-doc@test.local", "MAINTENANCE_MANAGER"))
    created = client.post(
        "/api/v1/documents/",
        {
            "title": "Flight manual",
            "file_name": "manual.pdf",
            "storage_key": "DOC-MAN-001",
            "document_type": "MANUAL",
            "uav": str(uav.id),
        },
        format="json",
    )
    assert created.status_code == 201
    assert created.json()["data"]["uav_registration"] == "TR-DOC-001"

    listed = client.get(f"/api/v1/documents/?uav={uav.id}")
    assert listed.status_code == 200
    assert listed.json()["meta"]["total"] == 1


@pytest.mark.django_db
def test_document_requires_target(rbac):
    client = _auth_client(_user("mgr-doc2@test.local", "MAINTENANCE_MANAGER"))
    created = client.post(
        "/api/v1/documents/",
        {
            "title": "Orphan",
            "file_name": "x.pdf",
            "storage_key": "DOC-ORPHAN",
            "document_type": "OTHER",
        },
        format="json",
    )
    assert created.status_code == 400
    assert created.json()["error"]["code"] == "DOCUMENT_TARGET_REQUIRED"


@pytest.mark.django_db
def test_viewer_cannot_create_document(rbac, uav):
    client = _auth_client(_user("viewer-doc@test.local", "VIEWER"))
    created = client.post(
        "/api/v1/documents/",
        {
            "title": "No",
            "file_name": "no.pdf",
            "storage_key": "DOC-NO",
            "uav": str(uav.id),
        },
        format="json",
    )
    assert created.status_code == 403


@pytest.mark.django_db
def test_manager_uploads_and_downloads_file(rbac, uav, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    client = _auth_client(_user("mgr-up@test.local", "MAINTENANCE_MANAGER"))
    created = client.post(
        "/api/v1/documents/",
        {
            "title": "Wing photo",
            "document_type": "PHOTO",
            "uav": str(uav.id),
            "file": SimpleUploadedFile("wing.jpg", b"\xff\xd8fakejpeg", content_type="image/jpeg"),
        },
        format="multipart",
    )
    assert created.status_code == 201
    data = created.json()["data"]
    assert data["has_file"] is True
    assert data["file_name"] == "wing.jpg"
    assert data["storage_key"].startswith("DOC-")

    download = client.get(f"/api/v1/documents/{data['id']}/download/")
    assert download.status_code == 200
    content = b"".join(download.streaming_content)
    assert content == b"\xff\xd8fakejpeg"


@pytest.mark.django_db
def test_upload_rejects_disallowed_type(rbac, uav, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    client = _auth_client(_user("mgr-bad@test.local", "MAINTENANCE_MANAGER"))
    created = client.post(
        "/api/v1/documents/",
        {
            "title": "Script",
            "document_type": "OTHER",
            "uav": str(uav.id),
            "file": SimpleUploadedFile("run.exe", b"MZ", content_type="application/octet-stream"),
        },
        format="multipart",
    )
    assert created.status_code == 400
    assert created.json()["error"]["code"] == "DOCUMENT_FILE_TYPE_INVALID"


@pytest.mark.django_db
@override_settings(DOCUMENT_MAX_BYTES=8)
def test_upload_rejects_oversized_file(rbac, uav, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    client = _auth_client(_user("mgr-big@test.local", "MAINTENANCE_MANAGER"))
    created = client.post(
        "/api/v1/documents/",
        {
            "title": "Big",
            "document_type": "OTHER",
            "uav": str(uav.id),
            "file": SimpleUploadedFile("notes.txt", b"0123456789", content_type="text/plain"),
        },
        format="multipart",
    )
    assert created.status_code == 400
    assert created.json()["error"]["code"] == "DOCUMENT_FILE_TOO_LARGE"


@pytest.mark.django_db
def test_download_missing_file(rbac, uav):
    client = _auth_client(_user("mgr-miss@test.local", "MAINTENANCE_MANAGER"))
    created = client.post(
        "/api/v1/documents/",
        {
            "title": "Metadata only",
            "file_name": "ghost.pdf",
            "storage_key": "DOC-GHOST",
            "document_type": "MANUAL",
            "uav": str(uav.id),
        },
        format="json",
    )
    document_id = created.json()["data"]["id"]
    download = client.get(f"/api/v1/documents/{document_id}/download/")
    assert download.status_code == 409
    assert download.json()["error"]["code"] == "DOCUMENT_FILE_MISSING"
