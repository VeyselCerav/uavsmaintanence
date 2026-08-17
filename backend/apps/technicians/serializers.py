from rest_framework import serializers

from apps.accounts.models import User
from apps.technicians.models import Skill, Technician, TechnicianCertification, TechnicianSkill


class SkillSerializer(serializers.ModelSerializer):
    code = serializers.CharField(max_length=64)

    class Meta:
        model = Skill
        fields = (
            "id",
            "code",
            "name",
            "description",
            "is_active",
            "is_demo",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("is_demo",)
        validators = []


class TechnicianSkillSerializer(serializers.ModelSerializer):
    skill_id = serializers.UUIDField(source="skill.id", read_only=True)
    skill_code = serializers.CharField(source="skill.code", read_only=True)
    skill_name = serializers.CharField(source="skill.name", read_only=True)
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects.all(), write_only=True)

    class Meta:
        model = TechnicianSkill
        fields = (
            "id",
            "skill",
            "skill_id",
            "skill_code",
            "skill_name",
            "certified_at",
            "expires_at",
            "created_at",
            "updated_at",
        )
        validators = []


class TechnicianCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicianCertification
        fields = (
            "id",
            "name",
            "issuer",
            "issued_at",
            "expires_at",
            "document_id",
            "created_at",
            "updated_at",
        )


class TechnicianSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    role = serializers.CharField(source="user.role.code", read_only=True, allow_null=True)
    user_id = serializers.UUIDField(source="user.id", read_only=True)
    skills = TechnicianSkillSerializer(many=True, read_only=True)
    certifications = TechnicianCertificationSerializer(many=True, read_only=True)

    class Meta:
        model = Technician
        fields = (
            "id",
            "user_id",
            "employee_number",
            "status",
            "notes",
            "is_demo",
            "email",
            "full_name",
            "role",
            "skills",
            "certifications",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("is_demo",)


class TechnicianWriteSerializer(serializers.Serializer):
    employee_number = serializers.CharField(max_length=64, required=False)
    status = serializers.CharField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    email = serializers.EmailField(required=False)
    full_name = serializers.CharField(required=False, max_length=255)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    is_demo = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if self.instance is None:
            if not attrs.get("employee_number"):
                raise serializers.ValidationError({"employee_number": "required"})
            if not attrs.get("user") and not (
                attrs.get("email") and attrs.get("full_name") and attrs.get("password")
            ):
                raise serializers.ValidationError(
                    {"email": "email, full_name and password are required without user"}
                )
        return attrs
