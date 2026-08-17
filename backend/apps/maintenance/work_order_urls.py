from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.maintenance.work_order_views import WorkOrderViewSet
from apps.parts.views import WorkOrderPartViewSet

router = DefaultRouter()
router.register("", WorkOrderViewSet, basename="work-order")

urlpatterns = [
    path(
        "<uuid:work_order_id>/parts/",
        WorkOrderPartViewSet.as_view({"get": "list", "post": "create"}),
        name="work-order-part-list",
    ),
    path(
        "<uuid:work_order_id>/parts/<uuid:pk>/",
        WorkOrderPartViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="work-order-part-detail",
    ),
    *router.urls,
]
