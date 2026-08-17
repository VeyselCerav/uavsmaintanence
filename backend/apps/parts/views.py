from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets

from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode
from apps.maintenance.models import WorkOrder
from apps.parts.models import CostRecord, Part, PartCompatibility, WorkOrderPart
from apps.parts.serializers import (
    CostRecordSerializer,
    PartCompatibilitySerializer,
    PartSerializer,
    WorkOrderPartSerializer,
)
from apps.parts.services import (
    CostRecordService,
    PartCompatibilityService,
    PartService,
    WorkOrderPartService,
)


class PartViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = PartSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "part.view",
        "retrieve": "part.view",
        "create": "part.create",
        "update": "part.update",
        "partial_update": "part.update",
        "destroy": "part.delete",
    }

    def get_queryset(self):
        queryset = Part.objects.prefetch_related(
            Prefetch(
                "compatibilities",
                queryset=PartCompatibility.objects.select_related(
                    "uav_class",
                    "platform_type",
                    "component_type",
                ),
            )
        )
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(part_number__icontains=search)
                | Q(name__icontains=search)
                | Q(manufacturer__icontains=search)
            )
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("part_number")

    def perform_create(self, serializer):
        part = PartService.create(actor=self.request.user, validated_data=serializer.validated_data)
        serializer.instance = part

    def perform_update(self, serializer):
        part = PartService.update(
            actor=self.request.user,
            part=serializer.instance,
            validated_data=serializer.validated_data,
        )
        serializer.instance = part


class PartCompatibilityViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = PartCompatibilitySerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "delete", "head", "options"]
    permission_map = {
        "list": "part.view",
        "retrieve": "part.view",
        "create": "part.update",
        "destroy": "part.update",
    }

    def get_part(self) -> Part:
        return get_object_or_404(Part, pk=self.kwargs["part_id"])

    def get_queryset(self):
        return (
            PartCompatibility.objects.filter(part_id=self.kwargs["part_id"])
            .select_related("uav_class", "platform_type", "component_type")
            .order_by("created_at")
        )

    def perform_create(self, serializer):
        row = PartCompatibilityService.create(
            actor=self.request.user,
            part=self.get_part(),
            validated_data=serializer.validated_data,
        )
        serializer.instance = row

    def perform_destroy(self, instance):
        PartCompatibilityService.delete(actor=self.request.user, row=instance)


class CostRecordViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = CostRecordSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "cost.view",
        "retrieve": "cost.view",
        "create": "work_order.update",
        "update": "work_order.update",
        "partial_update": "work_order.update",
        "destroy": "work_order.update",
    }

    def get_queryset(self):
        queryset = CostRecord.objects.select_related("uav", "work_order", "component")
        uav_id = self.request.query_params.get("uav")
        if uav_id:
            queryset = queryset.filter(uav_id=uav_id)
        work_order_id = self.request.query_params.get("work_order")
        if work_order_id:
            queryset = queryset.filter(work_order_id=work_order_id)
        return queryset.order_by("-occurred_at")

    def perform_create(self, serializer):
        record = CostRecordService.create(
            actor=self.request.user,
            validated_data=serializer.validated_data,
        )
        serializer.instance = record

    def perform_update(self, serializer):
        record = CostRecordService.update(
            actor=self.request.user,
            record=serializer.instance,
            validated_data=serializer.validated_data,
        )
        serializer.instance = record


class WorkOrderPartViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = WorkOrderPartSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "delete", "head", "options"]
    permission_map = {
        "list": "work_order.view",
        "retrieve": "work_order.view",
        "create": "work_order.update",
        "destroy": "work_order.update",
    }

    def get_work_order(self) -> WorkOrder:
        return get_object_or_404(
            WorkOrder.objects.select_related("uav", "component"),
            pk=self.kwargs["work_order_id"],
        )

    def get_queryset(self):
        return (
            WorkOrderPart.objects.filter(work_order_id=self.kwargs["work_order_id"])
            .select_related("part")
            .order_by("created_at")
        )

    def perform_create(self, serializer):
        line = WorkOrderPartService.create(
            actor=self.request.user,
            work_order=self.get_work_order(),
            validated_data=serializer.validated_data,
        )
        serializer.instance = line

    def perform_destroy(self, instance):
        WorkOrderPartService.delete(actor=self.request.user, line=instance)
