from django.contrib import admin

from apps.technicians.models import Skill, Technician, TechnicianCertification, TechnicianSkill


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ("employee_number", "user", "status", "is_demo")
    list_filter = ("status", "is_demo")
    search_fields = ("employee_number", "user__email", "user__full_name")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "is_demo")
    list_filter = ("is_active", "is_demo")
    search_fields = ("code", "name")


@admin.register(TechnicianSkill)
class TechnicianSkillAdmin(admin.ModelAdmin):
    list_display = ("technician", "skill", "certified_at", "expires_at")
    search_fields = ("technician__employee_number", "skill__code")


@admin.register(TechnicianCertification)
class TechnicianCertificationAdmin(admin.ModelAdmin):
    list_display = ("technician", "name", "issuer", "document_id", "issued_at", "expires_at")
    search_fields = ("technician__employee_number", "name", "issuer", "document_id")
