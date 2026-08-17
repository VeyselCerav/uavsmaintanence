from rest_framework.routers import DefaultRouter

from apps.accounts.user_views import RoleViewSet

router = DefaultRouter()
router.register("", RoleViewSet, basename="role")

urlpatterns = router.urls
