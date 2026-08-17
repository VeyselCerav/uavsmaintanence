from django.contrib import admin

from apps.uavs.models import UAV, MissionType, PlatformType, UAVClass


@admin.register(UAVClass)
class UAVClassAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "is_demo")


@admin.register(PlatformType)
class PlatformTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")


@admin.register(MissionType)
class MissionTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")


@admin.register(UAV)
class UAVAdmin(admin.ModelAdmin):
    list_display = ("registration_number", "model", "status", "maintenance_approach", "is_demo")
    list_filter = ("status", "maintenance_approach", "is_demo")
    search_fields = ("registration_number", "serial_number")
