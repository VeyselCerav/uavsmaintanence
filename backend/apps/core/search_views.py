from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import HasPermissionCode
from apps.core.search_services import SearchService


class SearchView(APIView):
    permission_classes = [HasPermissionCode]
    permission_map = {"get": "dashboard.view"}

    def initial(self, request, *args, **kwargs):
        self.action = request.method.lower()
        super().initial(request, *args, **kwargs)

    def get(self, request):
        data = SearchService.search(user=request.user, query=request.query_params.get("q") or "")
        return Response({"success": True, "data": data})
