from rest_framework.routers import DefaultRouter

from apps.flights.views import FlightViewSet

router = DefaultRouter()
router.register("", FlightViewSet, basename="flight")

urlpatterns = router.urls
