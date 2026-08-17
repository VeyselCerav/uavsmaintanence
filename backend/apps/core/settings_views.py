from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import HasPermissionCode
from apps.core.settings_serializers import SettingPatchSerializer
from apps.core.settings_services import SettingsService


class SettingsView(APIView):
    permission_classes = [HasPermissionCode]
    permission_map = {
        "get": "settings.view",
        "patch": "settings.update",
        "put": "settings.update",
    }

    def initial(self, request, *args, **kwargs):
        self.action = request.method.lower()
        super().initial(request, *args, **kwargs)

    def get(self, request):
        return Response({"success": True, "data": SettingsService.list_payload()})

    def patch(self, request):
        serializer = SettingPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = SettingsService.update(
            actor=request.user,
            key=serializer.validated_data["key"],
            value=serializer.validated_data["value"],
            request=request,
        )
        return Response({"success": True, "data": data})

    def put(self, request):
        return self.patch(request)
