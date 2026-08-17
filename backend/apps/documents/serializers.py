from rest_framework import serializers

from apps.documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    uav_registration = serializers.SerializerMethodField()
    component_name = serializers.SerializerMethodField()
    template_code = serializers.SerializerMethodField()
    work_order_number = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()
    has_file = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Document
        fields = (
            "id",
            "title",
            "file_name",
            "content_type",
            "size_bytes",
            "storage_key",
            "has_file",
            "file",
            "document_type",
            "uav",
            "uav_registration",
            "component",
            "component_name",
            "template",
            "template_code",
            "work_order",
            "work_order_number",
            "uploaded_by",
            "uploaded_by_name",
            "notes",
            "is_demo",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uploaded_by", "is_demo", "has_file")
        extra_kwargs = {
            "uav": {"required": False, "allow_null": True},
            "component": {"required": False, "allow_null": True},
            "template": {"required": False, "allow_null": True},
            "work_order": {"required": False, "allow_null": True},
            "content_type": {"required": False, "allow_blank": True},
            "size_bytes": {"required": False},
            "notes": {"required": False, "allow_blank": True},
            "file_name": {"required": False, "allow_blank": True},
            "storage_key": {"required": False, "allow_blank": True},
        }

    def get_uav_registration(self, obj) -> str:
        return obj.uav.registration_number if obj.uav_id else ""

    def get_component_name(self, obj) -> str:
        return obj.component.name if obj.component_id else ""

    def get_template_code(self, obj) -> str:
        return obj.template.code if obj.template_id else ""

    def get_work_order_number(self, obj) -> str:
        return obj.work_order.number if obj.work_order_id else ""

    def get_uploaded_by_name(self, obj) -> str:
        return obj.uploaded_by.full_name if obj.uploaded_by_id else ""

    def get_has_file(self, obj) -> bool:
        return bool(obj.file)
