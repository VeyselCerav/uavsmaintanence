from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.fmea.views import FMEAItemViewSet, FMEAViewSet

router = DefaultRouter()
router.register("", FMEAViewSet, basename="fmea")

urlpatterns = [
    path(
        "<uuid:fmea_id>/items/",
        FMEAItemViewSet.as_view({"get": "list", "post": "create"}),
        name="fmea-item-list",
    ),
    path(
        "<uuid:fmea_id>/items/<uuid:pk>/",
        FMEAItemViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="fmea-item-detail",
    ),
    *router.urls,
]
