from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "user",
            "user_email",
            "user_name",
            "timestamp",
            "ip",
            "action",
            "entity_type",
            "entity_id",
            "old_value",
            "new_value",
            "message",
        )
        read_only_fields = fields

    def get_user_email(self, obj) -> str:
        return obj.user.email if obj.user_id else ""

    def get_user_name(self, obj) -> str:
        return obj.user.full_name if obj.user_id else ""
