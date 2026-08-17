from django.db.models import Q
from django.http import FileResponse
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode
from apps.documents.models import Document
from apps.documents.serializers import DocumentSerializer
from apps.documents.services import DocumentService


class DocumentViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "document.view",
        "retrieve": "document.view",
        "create": "document.create",
        "update": "document.create",
        "partial_update": "document.create",
        "destroy": "document.delete",
        "download": "document.view",
    }

    def get_queryset(self):
        queryset = Document.objects.select_related(
            "uav",
            "component",
            "template",
            "work_order",
            "uploaded_by",
        )
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(file_name__icontains=search)
                | Q(storage_key__icontains=search)
            )
        for field, param in (
            ("uav_id", "uav"),
            ("work_order_id", "work_order"),
            ("template_id", "template"),
            ("component_id", "component"),
        ):
            value = self.request.query_params.get(param)
            if value:
                queryset = queryset.filter(**{field: value})
        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        document = DocumentService.create(
            actor=self.request.user,
            validated_data=serializer.validated_data,
        )
        serializer.instance = document

    def perform_update(self, serializer):
        document = DocumentService.update(
            actor=self.request.user,
            document=serializer.instance,
            validated_data=serializer.validated_data,
        )
        serializer.instance = document

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        document = self.get_object()
        handle = DocumentService.open_file(document)
        return FileResponse(
            handle,
            as_attachment=True,
            filename=document.file_name or "document",
            content_type=document.content_type or "application/octet-stream",
        )
