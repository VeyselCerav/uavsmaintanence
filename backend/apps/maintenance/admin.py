from django.contrib import admin

from apps.maintenance.models import MaintenanceTemplate


@admin.register(MaintenanceTemplate)
class MaintenanceTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "approach", "is_active", "is_demo")
    list_filter = ("approach", "is_demo", "is_active")
