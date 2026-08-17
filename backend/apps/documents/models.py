import uuid
from pathlib import Path

from django.db import models
from django.db.models import Q
from django.utils.text import get_valid_filename

from apps.core.models import SoftDeleteModel
from apps.documents.enums import DocumentType


def document_upload_to(instance, filename: str) -> str:
    name = get_valid_filename(Path(filename).name)[:80] or "file"
    return f"documents/{uuid.uuid4().hex}/{name}"


class Document(SoftDeleteModel):
    title = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=128, blank=True)
    size_bytes = models.PositiveIntegerField(default=0)
    storage_key = models.CharField(max_length=255)
    file = models.FileField(upload_to=document_upload_to, blank=True)
    document_type = models.CharField(
        max_length=16,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
    )
    uav = models.ForeignKey(
        "uavs.UAV",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    component = models.ForeignKey(
        "components.UAVComponent",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    template = models.ForeignKey(
        "maintenance.MaintenanceTemplate",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    work_order = models.ForeignKey(
        "maintenance.WorkOrder",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    uploaded_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_documents",
    )
    notes = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "document"
        indexes = [
            models.Index(fields=["uav", "-created_at"]),
            models.Index(fields=["work_order"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["storage_key"],
                condition=Q(is_deleted=False),
                name="uniq_document_storage_key_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.title
