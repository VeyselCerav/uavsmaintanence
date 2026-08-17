from django.urls import path

from apps.core.dashboard_views import DashboardViewSet

urlpatterns = [
    path("", DashboardViewSet.as_view({"get": "list"})),
]
