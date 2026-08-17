from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode
from apps.maintenance.models import MaintenanceTemplate, MaintenanceTemplateItem
from apps.maintenance.serializers import (
    MaintenanceTemplateItemSerializer,
    MaintenanceTemplateSerializer,
)
from apps.maintenance.services import (
    MaintenanceDueService,
    TemplateItemService,
    TemplateResolveService,
)


class ResolvePermission(HasPermissionCode):
    def has_permission(self, request, view):
        view.action = "resolve"
        view.permission_map = {"resolve": "uav.view"}
        return super().has_permission(request, view)


@api_view(["GET"])
@permission_classes([ResolvePermission])
def resolve_template(request):
    uav_class = request.query_params.get("uav_class")
    platform = request.query_params.get("platform")
    mission = request.query_params.get("mission")
    approach = request.query_params.get("approach")
    if not all([uav_class, platform, mission, approach]):
        raise ValidationError(
            {
                "code": "missing_query",
                "message_key": "errors.maintenance.resolve_params",
            }
        )
    template = TemplateResolveService.resolve(uav_class, platform, mission, approach)
    data = MaintenanceTemplateSerializer(template).data
    return Response({"success": True, "data": data})


class MaintenanceTemplateViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = MaintenanceTemplateSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "maintenance_template.view",
        "retrieve": "maintenance_template.view",
        "create": "maintenance_template.create",
        "update": "maintenance_template.update",
        "partial_update": "maintenance_template.update",
        "destroy": "maintenance_template.delete",
    }

    def get_queryset(self):
        queryset = (
            MaintenanceTemplate.objects.select_related(
                "uav_class",
                "platform_type",
                "mission_type",
            )
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=MaintenanceTemplateItem.objects.select_related("component_type"),
                )
            )
            .annotate(item_count=Count("items", filter=Q(items__is_deleted=False)))
        )
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(code__icontains=search) | Q(name__icontains=search))
        return queryset.order_by("code")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
        MaintenanceDueService.recalculate_template(serializer.instance)

    def perform_destroy(self, instance):
        instance.delete()
        MaintenanceDueService.recalculate_template(instance)


class TemplateItemViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = MaintenanceTemplateItemSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "maintenance_template.view",
        "retrieve": "maintenance_template.view",
        "create": "maintenance_template.update",
        "update": "maintenance_template.update",
        "partial_update": "maintenance_template.update",
        "destroy": "maintenance_template.update",
        "reorder": "maintenance_template.update",
    }

    def get_template(self) -> MaintenanceTemplate:
        return get_object_or_404(MaintenanceTemplate, pk=self.kwargs["template_id"])

    def get_queryset(self):
        return MaintenanceTemplateItem.objects.filter(
            template_id=self.kwargs["template_id"]
        ).select_related("component_type").order_by("sequence", "task_code")

    def perform_create(self, serializer):
        item = TemplateItemService.create(
            actor=self.request.user,
            template=self.get_template(),
            validated_data=serializer.validated_data,
        )
        serializer.instance = item

    def perform_update(self, serializer):
        item = TemplateItemService.update(
            actor=self.request.user,
            item=serializer.instance,
            validated_data=serializer.validated_data,
        )
        serializer.instance = item

    def perform_destroy(self, instance):
        TemplateItemService.delete(actor=self.request.user, item=instance)

    @action(detail=False, methods=["post"])
    def reorder(self, request, template_id=None):
        item_ids = request.data.get("item_ids") or []
        items = TemplateItemService.reorder(
            actor=request.user,
            template=self.get_template(),
            item_ids=item_ids,
        )
        data = MaintenanceTemplateItemSerializer(items, many=True).data
        return Response({"success": True, "data": data})
