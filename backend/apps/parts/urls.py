from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.parts.views import PartCompatibilityViewSet, PartViewSet

router = DefaultRouter()
router.register("", PartViewSet, basename="part")

urlpatterns = [
    path(
        "<uuid:part_id>/compatibility/",
        PartCompatibilityViewSet.as_view({"get": "list", "post": "create"}),
        name="part-compatibility-list",
    ),
    path(
        "<uuid:part_id>/compatibility/<uuid:pk>/",
        PartCompatibilityViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="part-compatibility-detail",
    ),
    *router.urls,
]
