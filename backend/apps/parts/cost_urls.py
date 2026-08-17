from rest_framework.routers import DefaultRouter

from apps.parts.views import CostRecordViewSet

router = DefaultRouter()
router.register("", CostRecordViewSet, basename="cost")

urlpatterns = router.urls
