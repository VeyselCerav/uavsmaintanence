from django.contrib import admin

from apps.fmea.models import FMEA, FMEAItem


@admin.register(FMEA)
class FMEAAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "status", "revision", "is_demo")
    list_filter = ("status", "is_demo")
    search_fields = ("code", "title")


@admin.register(FMEAItem)
class FMEAItemAdmin(admin.ModelAdmin):
    list_display = ("fmea", "sequence", "function", "rpn", "catalog_mode")
    search_fields = ("function", "failure_mode", "fmea__code")
