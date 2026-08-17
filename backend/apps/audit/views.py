from django.db.models import Q
from rest_framework import viewsets

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode


class AuditLogViewSet(EnvelopeMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "head", "options"]
    permission_map = {
        "list": "audit.view",
        "retrieve": "audit.view",
    }

    def get_queryset(self):
        queryset = AuditLog.objects.select_related("user")
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(entity_type__icontains=search)
                | Q(action__icontains=search)
                | Q(message__icontains=search)
                | Q(user__email__icontains=search)
            )
        entity_type = self.request.query_params.get("entity_type")
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        action = self.request.query_params.get("action")
        if action:
            queryset = queryset.filter(action=action)
        return queryset.order_by("-timestamp")
