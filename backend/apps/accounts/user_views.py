from django.db.models import Q
from rest_framework import viewsets

from apps.accounts.models import Role
from apps.accounts.user_serializers import RoleSerializer, UserSerializer
from apps.accounts.user_services import UserService
from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode


class RoleViewSet(EnvelopeMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Role.objects.all().order_by("code")
    serializer_class = RoleSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "head", "options"]
    permission_map = {
        "list": "role.view",
        "retrieve": "role.view",
    }


class UserViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "user.view",
        "retrieve": "user.view",
        "create": "user.create",
        "update": "user.update",
        "partial_update": "user.update",
        "destroy": "user.delete",
    }

    def get_queryset(self):
        queryset = UserService.alive()
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | Q(full_name__icontains=search)
            )
        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(role__code=role)
        return queryset.order_by("email")

    def perform_create(self, serializer):
        user = UserService.create(
            actor=self.request.user,
            data=serializer.validated_data,
            request=self.request,
        )
        serializer.instance = user

    def perform_update(self, serializer):
        user = UserService.update(
            actor=self.request.user,
            user=serializer.instance,
            data=serializer.validated_data,
            request=self.request,
        )
        serializer.instance = user

    def perform_destroy(self, instance):
        UserService.delete(actor=self.request.user, user=instance, request=self.request)
