from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer
from apps.notifications.services import NotificationService


class NotificationViewSet(EnvelopeMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "head", "options"]
    permission_map = {
        "list": "notification.view",
        "retrieve": "notification.view",
        "unread_count": "notification.view",
        "read": "notification.view",
        "read_all": "notification.view",
    }

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        unread = self.request.query_params.get("unread")
        if unread in {"1", "true", "True"}:
            queryset = queryset.filter(is_read=False)
        return queryset.order_by("-created_at")

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"success": True, "data": {"unread": count}})

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        notification = NotificationService.mark_read(notification=self.get_object())
        data = NotificationSerializer(notification).data
        return Response({"success": True, "data": data})

    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        updated = NotificationService.mark_all_read(user=request.user)
        return Response({"success": True, "data": {"updated": updated}})
