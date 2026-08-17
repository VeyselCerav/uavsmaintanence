from rest_framework.routers import DefaultRouter

from apps.uavs.views import MissionTypeViewSet

router = DefaultRouter()
router.register("", MissionTypeViewSet, basename="mission")

urlpatterns = router.urls
