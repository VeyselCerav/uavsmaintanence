from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode
from apps.rcm.models import RCMAnalysis, RCMItem
from apps.rcm.serializers import RCMAnalysisSerializer, RCMItemSerializer
from apps.rcm.services import RCMItemService, RCMService
from apps.uavs.models import UAV


class RCMAnalysisViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = RCMAnalysisSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "rcm.view",
        "retrieve": "rcm.view",
        "create": "rcm.create",
        "update": "rcm.update",
        "partial_update": "rcm.update",
        "destroy": "rcm.update",
        "approve": "rcm.approve",
        "evaluate": "rcm.update",
        "apply_to_template": "rcm.update",
    }

    def get_queryset(self):
        queryset = (
            RCMAnalysis.objects.select_related(
                "uav_class",
                "platform_type",
                "component_type",
                "mission_type",
                "approved_by",
            )
            .prefetch_related(
                Prefetch("items", queryset=RCMItem.objects.select_related("fmea_item"))
            )
            .annotate(item_count=Count("items", filter=Q(items__is_deleted=False)))
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
        analysis = RCMService.create(
            actor=self.request.user,
            validated_data=serializer.validated_data,
        )
        serializer.instance = analysis

    def perform_update(self, serializer):
        analysis = RCMService.update(
            actor=self.request.user,
            analysis=serializer.instance,
            validated_data=serializer.validated_data,
        )
        serializer.instance = analysis

    def perform_destroy(self, instance):
        RCMService.ensure_editable(instance)
        instance.delete()

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        analysis = RCMService.approve(actor=request.user, analysis=self.get_object())
        return Response({"success": True, "data": RCMAnalysisSerializer(analysis).data})

    @action(detail=True, methods=["post"])
    def evaluate(self, request, pk=None):
        analysis = RCMService.evaluate(actor=request.user, analysis=self.get_object())
        return Response({"success": True, "data": RCMAnalysisSerializer(analysis).data})

    @action(detail=True, methods=["post"], url_path="apply-to-template")
    def apply_to_template(self, request, pk=None):
        result = RCMService.apply_to_template(actor=request.user, analysis=self.get_object())
        return Response({"success": True, "data": result})


class RCMItemViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = RCMItemSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "rcm.view",
        "retrieve": "rcm.view",
        "create": "rcm.update",
        "update": "rcm.update",
        "partial_update": "rcm.update",
        "destroy": "rcm.update",
    }

    def get_analysis(self) -> RCMAnalysis:
        return get_object_or_404(RCMAnalysis, pk=self.kwargs["rcm_id"])

    def get_queryset(self):
        return (
            RCMItem.objects.filter(analysis_id=self.kwargs["rcm_id"])
            .select_related("fmea_item")
            .order_by("sequence", "created_at")
        )

    def perform_create(self, serializer):
        item = RCMItemService.create(
            actor=self.request.user,
            analysis=self.get_analysis(),
            validated_data=serializer.validated_data,
        )
        serializer.instance = item

    def perform_update(self, serializer):
        item = RCMItemService.update(
            actor=self.request.user,
            item=serializer.instance,
            validated_data=serializer.validated_data,
        )
        serializer.instance = item

    def perform_destroy(self, instance):
        RCMItemService.delete(actor=self.request.user, item=instance)
