from rest_framework.routers import DefaultRouter

from apps.technicians.views import SkillViewSet

router = DefaultRouter()
router.register("", SkillViewSet, basename="skill")

urlpatterns = router.urls
