from django.contrib import admin

from apps.rcm.models import RCMAnalysis, RCMItem


@admin.register(RCMAnalysis)
class RCMAnalysisAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "status", "revision", "is_demo")
    list_filter = ("status", "is_demo")
    search_fields = ("code", "title")


@admin.register(RCMItem)
class RCMItemAdmin(admin.ModelAdmin):
    list_display = ("analysis", "sequence", "function", "strategy", "is_overridden")
    search_fields = ("function", "failure_mode", "analysis__code")
