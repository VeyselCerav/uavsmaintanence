from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.components.models import ComponentType, UAVComponent
from apps.components.serializers import (
    ComponentTypeSerializer,
    UAVComponentInstallSerializer,
    UAVComponentRemoveSerializer,
    UAVComponentSerializer,
    UAVComponentUpdateSerializer,
)
from apps.components.services import ComponentService
from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode


class ComponentTypeViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    queryset = ComponentType.objects.all()
    serializer_class = ComponentTypeSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "component.view",
        "retrieve": "component.view",
        "create": "component.create",
        "update": "component.update",
        "partial_update": "component.update",
        "destroy": "component.delete",
    }

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


class UAVComponentViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = UAVComponentSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "head", "options"]
    permission_map = {
        "list": "component.view",
        "retrieve": "component.view",
        "create": "component.create",
        "update": "component.update",
        "partial_update": "component.update",
        "remove": "component.update",
    }

    def get_queryset(self):
        queryset = UAVComponent.objects.select_related("uav", "component_type")
        uav_id = self.request.query_params.get("uav")
        if uav_id:
            queryset = queryset.filter(uav_id=uav_id)
        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(serial_number__icontains=search)
                | Q(part_number__icontains=search)
            )
        return queryset.order_by("status", "name", "serial_number")

    def create(self, request, *args, **kwargs):
        serializer = UAVComponentInstallSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        component = ComponentService.install(
            actor=request.user,
            data=serializer.validated_data,
            request=request,
        )
        return Response(
            {"success": True, "data": UAVComponentSerializer(component).data},
            status=201,
        )

    def partial_update(self, request, *args, **kwargs):
        component = self.get_object()
        serializer = UAVComponentUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        component = ComponentService.update(
            actor=request.user,
            component=component,
            data=serializer.validated_data,
            request=request,
        )
        return Response({"success": True, "data": UAVComponentSerializer(component).data})

    @action(detail=True, methods=["post"])
    def remove(self, request, pk=None):
        serializer = UAVComponentRemoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        component = ComponentService.remove(
            actor=request.user,
            component=self.get_object(),
            data=serializer.validated_data,
            request=request,
        )
        return Response({"success": True, "data": UAVComponentSerializer(component).data})
