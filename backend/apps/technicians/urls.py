from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.technicians.views import (
    TechnicianCertificationViewSet,
    TechnicianSkillViewSet,
    TechnicianViewSet,
)

router = DefaultRouter()
router.register("", TechnicianViewSet, basename="technician")

urlpatterns = [
    path(
        "<uuid:technician_id>/skills/",
        TechnicianSkillViewSet.as_view({"get": "list", "post": "create"}),
        name="technician-skill-list",
    ),
    path(
        "<uuid:technician_id>/skills/<uuid:pk>/",
        TechnicianSkillViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="technician-skill-detail",
    ),
    path(
        "<uuid:technician_id>/certifications/",
        TechnicianCertificationViewSet.as_view({"get": "list", "post": "create"}),
        name="technician-certification-list",
    ),
    path(
        "<uuid:technician_id>/certifications/<uuid:pk>/",
        TechnicianCertificationViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="technician-certification-detail",
    ),
    *router.urls,
]
