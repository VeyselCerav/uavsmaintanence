from rest_framework.routers import DefaultRouter

from apps.components.views import UAVComponentViewSet

router = DefaultRouter()
router.register("", UAVComponentViewSet, basename="uav-component")

urlpatterns = router.urls
