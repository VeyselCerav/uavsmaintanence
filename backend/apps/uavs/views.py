from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode
from apps.uavs.models import UAV, MissionType, PlatformType, UAVClass
from apps.uavs.serializers import (
    MissionTypeSerializer,
    PlatformTypeSerializer,
    UAVClassSerializer,
    UAVSerializer,
)
from apps.uavs.services import UAVService
from apps.uavs.timeline import TimelineService


class CatalogViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(code__icontains=search))
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class UAVClassViewSet(CatalogViewSet):
    queryset = UAVClass.objects.all()
    serializer_class = UAVClassSerializer
    permission_map = {
        "list": "uav_class.view",
        "retrieve": "uav_class.view",
        "create": "uav_class.create",
        "update": "uav_class.update",
        "partial_update": "uav_class.update",
        "destroy": "uav_class.delete",
    }


class PlatformTypeViewSet(CatalogViewSet):
    queryset = PlatformType.objects.all()
    serializer_class = PlatformTypeSerializer
    permission_map = {
        "list": "platform.view",
        "retrieve": "platform.view",
        "create": "platform.create",
        "update": "platform.update",
        "partial_update": "platform.update",
        "destroy": "platform.delete",
    }


class MissionTypeViewSet(CatalogViewSet):
    queryset = MissionType.objects.all()
    serializer_class = MissionTypeSerializer
    permission_map = {
        "list": "mission.view",
        "retrieve": "mission.view",
        "create": "mission.create",
        "update": "mission.update",
        "partial_update": "mission.update",
        "destroy": "mission.delete",
    }


class UAVViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = UAVSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "uav.view",
        "retrieve": "uav.view",
        "create": "uav.create",
        "update": "uav.update",
        "partial_update": "uav.update",
        "destroy": "uav.delete",
        "timeline": "uav.view",
    }

    def get_queryset(self):
        queryset = UAV.objects.select_related(
            "uav_class",
            "platform_type",
            "mission_type",
            "maintenance_template",
        )
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(registration_number__icontains=search)
                | Q(serial_number__icontains=search)
                | Q(manufacturer__icontains=search)
                | Q(model__icontains=search)
            )
        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)
        return queryset.order_by("registration_number")

    def perform_create(self, serializer):
        uav = UAVService.create(actor=self.request.user, validated_data=serializer.validated_data)
        serializer.instance = UAVService.with_relations(uav)

    def perform_update(self, serializer):
        uav = UAVService.update(
            actor=self.request.user,
            uav=serializer.instance,
            validated_data=serializer.validated_data,
        )
        serializer.instance = UAVService.with_relations(uav)

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        events = TimelineService.for_uav(self.get_object())
        return Response({"success": True, "data": events, "meta": {"total": len(events)}})
