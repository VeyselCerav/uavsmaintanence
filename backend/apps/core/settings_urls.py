from django.urls import path

from apps.core.settings_views import SettingsView

urlpatterns = [
    path("", SettingsView.as_view(), name="system-settings"),
]
