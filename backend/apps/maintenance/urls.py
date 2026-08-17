from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.maintenance.views import (
    MaintenanceTemplateViewSet,
    TemplateItemViewSet,
    resolve_template,
)

router = DefaultRouter()
router.register("", MaintenanceTemplateViewSet, basename="maintenance-template")

urlpatterns = [
    path("resolve/", resolve_template, name="maintenance-template-resolve"),
    path(
        "<uuid:template_id>/items/reorder/",
        TemplateItemViewSet.as_view({"post": "reorder"}),
        name="maintenance-template-item-reorder",
    ),
    path(
        "<uuid:template_id>/items/",
        TemplateItemViewSet.as_view({"get": "list", "post": "create"}),
        name="maintenance-template-item-list",
    ),
    path(
        "<uuid:template_id>/items/<uuid:pk>/",
        TemplateItemViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="maintenance-template-item-detail",
    ),
    *router.urls,
]
