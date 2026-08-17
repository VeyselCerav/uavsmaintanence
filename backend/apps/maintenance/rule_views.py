from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import HasPermissionCode
from apps.maintenance.serializers import DueRulesSerializer
from apps.maintenance.services import DueRulesService


class DueRulesView(APIView):
    permission_classes = [HasPermissionCode]
    permission_map = {
        "get": "maintenance_rule.view",
        "put": "maintenance_rule.update",
        "patch": "maintenance_rule.update",
    }

    def initial(self, request, *args, **kwargs):
        self.action = request.method.lower()
        super().initial(request, *args, **kwargs)

    def get(self, request):
        return Response({"success": True, "data": DueRulesService.get_payload()})

    def patch(self, request):
        serializer = DueRulesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = DueRulesService.update(actor=request.user, validated_data=serializer.validated_data)
        return Response({"success": True, "data": data})

    def put(self, request):
        return self.patch(request)
