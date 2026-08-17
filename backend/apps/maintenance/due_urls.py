from rest_framework.routers import DefaultRouter

from apps.maintenance.due_views import MaintenanceDueViewSet

router = DefaultRouter()
router.register("", MaintenanceDueViewSet, basename="maintenance-due")

urlpatterns = router.urls
