from __future__ import annotations

import uuid
from pathlib import Path

from django.conf import settings
from django.db import IntegrityError

from apps.core.api_exceptions import (
    DocumentFileMissing,
    DocumentFileRequired,
    DocumentFileTooLarge,
    DocumentFileTypeInvalid,
    DocumentStorageKeyTaken,
    DocumentTargetRequired,
)
from apps.documents.models import Document


class DocumentService:
    @staticmethod
    def with_relations(document: Document) -> Document:
        return Document.objects.select_related(
            "uav",
            "component",
            "template",
            "work_order",
            "uploaded_by",
        ).get(pk=document.pk)

    @classmethod
    def ensure_target(cls, data: dict, *, existing: Document | None = None) -> None:
        uav = data["uav"] if "uav" in data else (existing.uav if existing else None)
        component = (
            data["component"] if "component" in data else (existing.component if existing else None)
        )
        template = (
            data["template"] if "template" in data else (existing.template if existing else None)
        )
        work_order = (
            data["work_order"]
            if "work_order" in data
            else (existing.work_order if existing else None)
        )
        if not any((uav, component, template, work_order)):
            raise DocumentTargetRequired()

    @classmethod
    def validate_upload(cls, upload) -> None:
        max_bytes = int(getattr(settings, "DOCUMENT_MAX_BYTES", 10 * 1024 * 1024))
        size = int(getattr(upload, "size", 0) or 0)
        if size > max_bytes:
            raise DocumentFileTooLarge()
        suffix = Path(getattr(upload, "name", "") or "").suffix.lower()
        allowed = tuple(getattr(settings, "DOCUMENT_ALLOWED_EXTENSIONS", ()))
        if suffix not in allowed:
            raise DocumentFileTypeInvalid()

    @classmethod
    def create(cls, *, actor, validated_data: dict) -> Document:
        cls.ensure_target(validated_data)
        upload = validated_data.pop("file", None)
        validated_data["title"] = (validated_data.get("title") or "").strip()
        if upload:
            cls.validate_upload(upload)
            validated_data["file"] = upload
            validated_data["file_name"] = Path(getattr(upload, "name", "file")).name[:255]
            validated_data["content_type"] = (getattr(upload, "content_type", None) or "")[:128]
            validated_data["size_bytes"] = int(getattr(upload, "size", 0) or 0)
            if not (validated_data.get("storage_key") or "").strip():
                validated_data["storage_key"] = f"DOC-{uuid.uuid4().hex[:20]}"
            else:
                validated_data["storage_key"] = validated_data["storage_key"].strip()
        else:
            validated_data["file_name"] = (validated_data.get("file_name") or "").strip()
            validated_data["storage_key"] = (validated_data.get("storage_key") or "").strip()
            if not validated_data["file_name"] or not validated_data["storage_key"]:
                raise DocumentFileRequired()
        document = Document(**validated_data)
        document.uploaded_by = actor
        document.created_by = actor
        document.updated_by = actor
        try:
            document.save()
        except IntegrityError as exc:
            raise DocumentStorageKeyTaken() from exc
        return cls.with_relations(document)

    @classmethod
    def update(cls, *, actor, document: Document, validated_data: dict) -> Document:
        cls.ensure_target(validated_data, existing=document)
        upload = validated_data.pop("file", None)
        if upload:
            cls.validate_upload(upload)
            validated_data["file"] = upload
            validated_data["file_name"] = Path(getattr(upload, "name", "file")).name[:255]
            validated_data["content_type"] = (getattr(upload, "content_type", None) or "")[:128]
            validated_data["size_bytes"] = int(getattr(upload, "size", 0) or 0)
        for field, value in validated_data.items():
            setattr(document, field, value)
        document.updated_by = actor
        try:
            document.save()
        except IntegrityError as exc:
            raise DocumentStorageKeyTaken() from exc
        return cls.with_relations(document)

    @classmethod
    def open_file(cls, document: Document):
        if not document.file:
            raise DocumentFileMissing()
        return document.file.open("rb")
