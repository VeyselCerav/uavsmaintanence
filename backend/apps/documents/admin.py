from django.contrib import admin

from apps.documents.models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "document_type", "storage_key", "uav", "is_demo")
    search_fields = ("title", "file_name", "storage_key")
