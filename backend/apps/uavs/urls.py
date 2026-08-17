from rest_framework.routers import DefaultRouter

from apps.uavs.views import UAVViewSet

router = DefaultRouter()
router.register("", UAVViewSet, basename="uav")

urlpatterns = router.urls
