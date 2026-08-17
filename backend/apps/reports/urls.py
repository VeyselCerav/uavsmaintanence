from django.urls import path

from apps.reports.views import ApproachComparisonView, ReportCatalogView, ReportPdfView, ReportXlsxView

urlpatterns = [
    path("", ReportCatalogView.as_view(), name="report-catalog"),
    path("comparison/", ApproachComparisonView.as_view(), name="report-comparison"),
    path("pdf/<str:report_type>/", ReportPdfView.as_view(), name="report-pdf"),
    path("xlsx/<str:report_type>/", ReportXlsxView.as_view(), name="report-xlsx"),
]
