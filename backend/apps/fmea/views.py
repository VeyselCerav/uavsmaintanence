from django.db.models import Count, Max, Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode
from apps.fmea.models import FMEA, FMEAItem
from apps.fmea.serializers import FMEAItemSerializer, FMEASerializer
from apps.fmea.services import FMEAItemService, FMEAService
from apps.uavs.models import UAV


class FMEAViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = FMEASerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "fmea.view",
        "retrieve": "fmea.view",
        "create": "fmea.create",
        "update": "fmea.update",
        "partial_update": "fmea.update",
        "destroy": "fmea.update",
        "approve": "fmea.approve",
    }

    def get_queryset(self):
        queryset = (
            FMEA.objects.select_related(
                "uav_class",
                "platform_type",
                "component_type",
                "mission_type",
                "approved_by",
            )
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=FMEAItem.objects.select_related("catalog_mode"),
                )
            )
            .annotate(
                item_count=Count("items", filter=Q(items__is_deleted=False)),
                max_rpn=Max("items__rpn", filter=Q(items__is_deleted=False)),
            )
        )
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(code__icontains=search) | Q(title__icontains=search))
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        for field, param in (
            ("uav_class_id", "uav_class"),
            ("platform_type_id", "platform"),
            ("component_type_id", "component_type"),
            ("mission_type_id", "mission"),
        ):
            value = self.request.query_params.get(param)
            if value:
                queryset = queryset.filter(**{field: value})
        uav_id = self.request.query_params.get("uav")
        if uav_id:
            uav = get_object_or_404(UAV, pk=uav_id)
            queryset = queryset.filter(
                uav_class_id=uav.uav_class_id,
                platform_type_id=uav.platform_type_id,
            ).filter(Q(mission_type_id=uav.mission_type_id) | Q(mission_type__isnull=True))
        return queryset.order_by("code")

    def perform_create(self, serializer):
        fmea = FMEAService.create(actor=self.request.user, validated_data=serializer.validated_data)
        serializer.instance = FMEAService.with_relations(fmea)

    def perform_update(self, serializer):
        fmea = FMEAService.update(
            actor=self.request.user,
            fmea=serializer.instance,
            validated_data=serializer.validated_data,
        )
        serializer.instance = fmea

    def perform_destroy(self, instance):
        FMEAService.ensure_editable(instance)
        instance.delete()

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        fmea = FMEAService.approve(actor=request.user, fmea=self.get_object())
        data = FMEASerializer(fmea).data
        return Response({"success": True, "data": data})


class FMEAItemViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = FMEAItemSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "fmea.view",
        "retrieve": "fmea.view",
        "create": "fmea.update",
        "update": "fmea.update",
        "partial_update": "fmea.update",
        "destroy": "fmea.update",
    }

    def get_fmea(self) -> FMEA:
        return get_object_or_404(FMEA, pk=self.kwargs["fmea_id"])

    def get_queryset(self):
        return (
            FMEAItem.objects.filter(fmea_id=self.kwargs["fmea_id"])
            .select_related("catalog_mode")
            .order_by("sequence", "created_at")
        )

    def perform_create(self, serializer):
        item = FMEAItemService.create(
            actor=self.request.user,
            fmea=self.get_fmea(),
            validated_data=serializer.validated_data,
        )
        serializer.instance = item

    def perform_update(self, serializer):
        item = FMEAItemService.update(
            actor=self.request.user,
            item=serializer.instance,
            validated_data=serializer.validated_data,
        )
        serializer.instance = item

    def perform_destroy(self, instance):
        FMEAItemService.delete(actor=self.request.user, item=instance)
