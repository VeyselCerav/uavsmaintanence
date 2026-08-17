from datetime import datetime, time, timedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode
from apps.maintenance.enums import ALERT_DUE_STATUSES
from apps.maintenance.models import MaintenanceDue
from apps.maintenance.serializers import MaintenanceDueSerializer
from apps.maintenance.services import MaintenanceDueService
from apps.uavs.models import UAV


def _day_bound(value: str | None, *, end: bool = False):
    if not value:
        return None
    parsed = parse_date(value)
    if parsed is None:
        return None
    moment = datetime.combine(parsed, time.min)
    if timezone.is_naive(moment):
        moment = timezone.make_aware(moment)
    if end:
        moment = moment + timedelta(days=1)
    return moment


class MaintenanceDueViewSet(EnvelopeMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = MaintenanceDueSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "head", "options"]
    permission_map = {
        "list": "maintenance.view",
        "retrieve": "maintenance.view",
        "recalculate": "maintenance.update",
    }

    def get_queryset(self):
        queryset = MaintenanceDue.objects.select_related(
            "uav",
            "component",
            "component__component_type",
            "template_item",
        )
        uav_id = self.request.query_params.get("uav")
        if uav_id:
            queryset = queryset.filter(uav_id=uav_id)
        status_value = self.request.query_params.get("status")
        if status_value == "attention":
            queryset = queryset.filter(status__in=ALERT_DUE_STATUSES)
        elif status_value:
            queryset = queryset.filter(status=status_value)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(uav__registration_number__icontains=search)
                | Q(template_item__task_code__icontains=search)
                | Q(template_item__task_name__icontains=search)
                | Q(component__serial_number__icontains=search)
            )
        due_from = _day_bound(self.request.query_params.get("due_from"))
        due_to = _day_bound(self.request.query_params.get("due_to"), end=True)
        if due_from is not None or due_to is not None:
            queryset = queryset.filter(due_at__isnull=False)
            if due_from is not None:
                queryset = queryset.filter(due_at__gte=due_from)
            if due_to is not None:
                queryset = queryset.filter(due_at__lt=due_to)
        return queryset.order_by("-usage_percent", "template_item__sequence")

    @action(detail=False, methods=["post"])
    def recalculate(self, request):
        uav_id = request.data.get("uav")
        if uav_id:
            uav = get_object_or_404(UAV, pk=uav_id)
            dues = MaintenanceDueService.recalculate(uav)
            data = MaintenanceDueSerializer(dues, many=True).data
            return Response({"success": True, "data": data})
        count = 0
        for uav in UAV.objects.all():
            MaintenanceDueService.recalculate(uav)
            count += 1
        return Response({"success": True, "data": {"uavs": count}})
