from django.contrib import admin

from apps.failures.models import Failure, FailureMode


@admin.register(FailureMode)
class FailureModeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "is_demo")
    list_filter = ("is_active", "is_demo")
    search_fields = ("code", "name")


@admin.register(Failure)
class FailureAdmin(admin.ModelAdmin):
    list_display = ("uav", "severity", "occurred_at", "resolved_at", "is_demo")
    list_filter = ("severity", "discovered_during", "is_demo")
    search_fields = ("description", "uav__registration_number", "failure_mode__code")
