from rest_framework import serializers

from apps.accounts.models import Role, User


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "code", "name", "description")
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    role_code = serializers.CharField(source="role.code", read_only=True, default="")
    role_name = serializers.CharField(source="role.name", read_only=True, default="")
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "locale",
            "timezone",
            "role",
            "role_code",
            "role_name",
            "is_active",
            "last_login_at",
            "created_at",
            "password",
        )
        extra_kwargs = {
            "role": {"required": False},
            "locale": {"required": False},
            "timezone": {"required": False},
            "is_active": {"required": False},
        }

    def validate(self, attrs):
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "This field is required."})
        if self.instance is None and not attrs.get("role"):
            raise serializers.ValidationError({"role": "This field is required."})
        return attrs
