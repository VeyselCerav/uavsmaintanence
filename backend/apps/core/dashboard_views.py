from rest_framework import viewsets
from rest_framework.response import Response

from apps.core.dashboard_services import DashboardService
from apps.core.permissions import HasPermissionCode


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [HasPermissionCode]
    pagination_class = None
    permission_map = {"list": "dashboard.view"}

    def list(self, request):
        return Response({"success": True, "data": DashboardService.build(user=request.user)})
