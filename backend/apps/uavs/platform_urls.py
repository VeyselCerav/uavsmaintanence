from rest_framework.routers import DefaultRouter

from apps.uavs.views import PlatformTypeViewSet

router = DefaultRouter()
router.register("", PlatformTypeViewSet, basename="platform")

urlpatterns = router.urls
