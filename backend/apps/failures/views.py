from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode
from apps.failures.models import Failure, FailureMode
from apps.failures.serializers import FailureModeSerializer, FailureSerializer
from apps.failures.services import FailureModeService, FailureService


class FailureModeViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    queryset = FailureMode.objects.all()
    serializer_class = FailureModeSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "failure.view",
        "retrieve": "failure.view",
        "create": "failure.create",
        "update": "failure.update",
        "partial_update": "failure.update",
        "destroy": "failure.delete",
    }

    def get_queryset(self):
        queryset = FailureMode.objects.all()
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(code__icontains=search))
        return queryset.order_by("code")

    def perform_create(self, serializer):
        mode = FailureModeService.create(actor=self.request.user, data=serializer.validated_data)
        serializer.instance = mode

    def perform_update(self, serializer):
        mode = FailureModeService.update(
            actor=self.request.user,
            mode=serializer.instance,
            data=serializer.validated_data,
        )
        serializer.instance = mode


class FailureViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = FailureSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "failure.view",
        "retrieve": "failure.view",
        "create": "failure.create",
        "update": "failure.update",
        "partial_update": "failure.update",
        "destroy": "failure.delete",
        "resolve": "failure.update",
    }

    def get_queryset(self):
        queryset = Failure.objects.select_related(
            "uav",
            "component",
            "failure_mode",
            "work_order",
        )
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search)
                | Q(uav__registration_number__icontains=search)
                | Q(failure_mode__code__icontains=search)
                | Q(failure_mode__name__icontains=search)
            )
        uav_id = self.request.query_params.get("uav")
        if uav_id:
            queryset = queryset.filter(uav_id=uav_id)
        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)
        discovered = self.request.query_params.get("discovered_during")
        if discovered:
            queryset = queryset.filter(discovered_during=discovered)
        status = self.request.query_params.get("status")
        if status == "open":
            queryset = queryset.filter(resolved_at__isnull=True)
        elif status == "resolved":
            queryset = queryset.filter(resolved_at__isnull=False)
        return queryset.order_by("-occurred_at")

    def perform_create(self, serializer):
        failure = FailureService.create(
            actor=self.request.user,
            validated_data=serializer.validated_data,
        )
        serializer.instance = failure

    def perform_update(self, serializer):
        failure = FailureService.update(
            actor=self.request.user,
            failure=serializer.instance,
            validated_data=serializer.validated_data,
        )
        serializer.instance = failure

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        failure = FailureService.resolve(
            actor=request.user,
            failure=self.get_object(),
            resolved_at=request.data.get("resolved_at"),
        )
        data = FailureSerializer(failure).data
        return Response({"success": True, "data": data})
