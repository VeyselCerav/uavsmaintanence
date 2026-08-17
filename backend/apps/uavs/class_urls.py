from rest_framework.routers import DefaultRouter

from apps.uavs.views import UAVClassViewSet

router = DefaultRouter()
router.register("", UAVClassViewSet, basename="uav-class")

urlpatterns = router.urls
