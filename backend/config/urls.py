from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def healthcheck(_request):
    return JsonResponse({"success": True, "data": {"status": "ok"}})


api_v1 = [
    path("auth/", include("apps.accounts.urls")),
    path("users/", include("apps.accounts.user_urls")),
    path("roles/", include("apps.accounts.role_urls")),
    path("settings/", include("apps.core.settings_urls")),
    path("dashboard/", include("apps.core.dashboard_urls")),
    path("search/", include("apps.core.search_urls")),
    path("uavs/", include("apps.uavs.urls")),
    path("uav-classes/", include("apps.uavs.class_urls")),
    path("platforms/", include("apps.uavs.platform_urls")),
    path("missions/", include("apps.uavs.mission_urls")),
    path("component-types/", include("apps.components.type_urls")),
    path("maintenance-templates/", include("apps.maintenance.urls")),
    path("maintenance-dues/", include("apps.maintenance.due_urls")),
    path("maintenance-records/", include("apps.maintenance.record_urls")),
    path("maintenance-rules/", include("apps.maintenance.rule_urls")),
    path("work-orders/", include("apps.maintenance.work_order_urls")),
    path("components/", include("apps.components.urls")),
    path("flights/", include("apps.flights.urls")),
    path("failures/", include("apps.failures.urls")),
    path("failure-modes/", include("apps.failures.mode_urls")),
    path("fmea/", include("apps.fmea.urls")),
    path("rcm/", include("apps.rcm.urls")),
    path("reliability/", include("apps.reliability.urls")),
    path("parts/", include("apps.parts.urls")),
    path("costs/", include("apps.parts.cost_urls")),
    path("technicians/", include("apps.technicians.urls")),
    path("skills/", include("apps.technicians.skill_urls")),
    path("documents/", include("apps.documents.urls")),
    path("reports/", include("apps.reports.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("audit/", include("apps.audit.urls")),
]

urlpatterns = [
    path("health/", healthcheck, name="health"),
    path("api/v1/", include(api_v1)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DJANGO_ADMIN_ENABLED:
    urlpatterns.insert(0, path("django-admin/", admin.site.urls))
