from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "action", "entity_type", "user", "ip")
    search_fields = ("entity_type", "message", "user__email")
    readonly_fields = (
        "user",
        "timestamp",
        "ip",
        "action",
        "entity_type",
        "entity_id",
        "old_value",
        "new_value",
        "message",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
