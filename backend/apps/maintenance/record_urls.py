from rest_framework.routers import DefaultRouter

from apps.maintenance.record_views import MaintenanceRecordViewSet

router = DefaultRouter()
router.register("", MaintenanceRecordViewSet, basename="maintenance-record")

urlpatterns = router.urls
