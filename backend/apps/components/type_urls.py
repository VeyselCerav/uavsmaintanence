from rest_framework.routers import DefaultRouter

from apps.components.views import ComponentTypeViewSet

router = DefaultRouter()
router.register("", ComponentTypeViewSet, basename="component-type")

urlpatterns = router.urls
