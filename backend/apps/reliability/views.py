from rest_framework import viewsets
from rest_framework.response import Response

from apps.core.permissions import HasPermissionCode
from apps.reliability.services import ReliabilityService


class ReliabilityViewSet(viewsets.ViewSet):
    permission_classes = [HasPermissionCode]
    pagination_class = None
    permission_map = {"list": "reliability.view"}

    def list(self, request):
        data = ReliabilityService.compute(
            scope=request.query_params.get("scope") or "fleet",
            scope_id=request.query_params.get("scope_id") or None,
            period_start=request.query_params.get("from") or None,
            period_end=request.query_params.get("to") or None,
        )
        return Response({"success": True, "data": data})
