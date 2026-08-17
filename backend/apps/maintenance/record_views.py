from django.db.models import Q
from rest_framework import viewsets

from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode
from apps.maintenance.models import MaintenanceRecord
from apps.maintenance.serializers import MaintenanceRecordSerializer


class MaintenanceRecordViewSet(EnvelopeMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "head", "options"]
    permission_map = {
        "list": "maintenance.view",
        "retrieve": "maintenance.view",
    }

    def get_queryset(self):
        queryset = MaintenanceRecord.objects.select_related(
            "work_order",
            "work_order__template_item",
            "uav",
            "component",
            "technician",
        )
        uav_id = self.request.query_params.get("uav")
        if uav_id:
            queryset = queryset.filter(uav_id=uav_id)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(work_order__number__icontains=search)
                | Q(uav__registration_number__icontains=search)
                | Q(description__icontains=search)
                | Q(technician__full_name__icontains=search)
            )
        return queryset.order_by("-performed_at")
