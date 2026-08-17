from django.urls import path

from apps.maintenance.rule_views import DueRulesView

urlpatterns = [
    path("", DueRulesView.as_view(), name="maintenance-rules"),
]
