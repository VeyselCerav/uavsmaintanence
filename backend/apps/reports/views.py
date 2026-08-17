from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import HasPermissionCode
from apps.reports.services import ReportService
from apps.maintenance.comparison_services import ApproachComparisonService


def _locale(request) -> str:
    return request.query_params.get("locale") or getattr(request.user, "locale", None) or "tr"


class ReportCatalogView(APIView):
    permission_classes = [HasPermissionCode]
    permission_map = {"get": "reports.view"}

    def initial(self, request, *args, **kwargs):
        self.action = request.method.lower()
        super().initial(request, *args, **kwargs)

    def get(self, request):
        return Response({"success": True, "data": ReportService.catalog()})


class ApproachComparisonView(APIView):
    permission_classes = [HasPermissionCode]
    permission_map = {"get": "reports.view"}

    def initial(self, request, *args, **kwargs):
        self.action = request.method.lower()
        super().initial(request, *args, **kwargs)

    def get(self, request):
        params = request.query_params
        data = ApproachComparisonService.compare(
            class_id=params.get("class") or None,
            platform_id=params.get("platform") or None,
            mission_id=params.get("mission") or None,
            period_start=params.get("from") or None,
            period_end=params.get("to") or None,
        )
        return Response({"success": True, "data": data})


class ReportPdfView(APIView):
    permission_classes = [HasPermissionCode]
    permission_map = {"get": "reports.export"}

    def initial(self, request, *args, **kwargs):
        self.action = request.method.lower()
        super().initial(request, *args, **kwargs)

    def get(self, request, report_type: str):
        payload, filename = ReportService.build_pdf(
            report_type=report_type,
            params=request.query_params,
            locale=_locale(request),
        )
        response = HttpResponse(payload, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ReportXlsxView(APIView):
    permission_classes = [HasPermissionCode]
    permission_map = {"get": "reports.export"}

    def initial(self, request, *args, **kwargs):
        self.action = request.method.lower()
        super().initial(request, *args, **kwargs)

    def get(self, request, report_type: str):
        payload, filename = ReportService.build_xlsx(
            report_type=report_type,
            params=request.query_params,
            locale=_locale(request),
        )
        response = HttpResponse(
            payload,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
