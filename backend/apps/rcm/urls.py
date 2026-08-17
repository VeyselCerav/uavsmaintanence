from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.rcm.views import RCMAnalysisViewSet, RCMItemViewSet

router = DefaultRouter()
router.register("", RCMAnalysisViewSet, basename="rcm")

urlpatterns = [
    path(
        "<uuid:rcm_id>/items/",
        RCMItemViewSet.as_view({"get": "list", "post": "create"}),
        name="rcm-item-list",
    ),
    path(
        "<uuid:rcm_id>/items/<uuid:pk>/",
        RCMItemViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="rcm-item-detail",
    ),
    *router.urls,
]
