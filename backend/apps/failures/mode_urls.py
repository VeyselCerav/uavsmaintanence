from rest_framework.routers import DefaultRouter

from apps.failures.views import FailureModeViewSet

router = DefaultRouter()
router.register("", FailureModeViewSet, basename="failure-mode")

urlpatterns = router.urls
