from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode
from apps.technicians.models import Skill, Technician, TechnicianCertification, TechnicianSkill
from apps.technicians.serializers import (
    SkillSerializer,
    TechnicianCertificationSerializer,
    TechnicianSerializer,
    TechnicianSkillSerializer,
    TechnicianWriteSerializer,
)
from apps.technicians.services import SkillService, TechnicianCapabilityService, TechnicianService


class TechnicianViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = TechnicianSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "head", "options"]
    permission_map = {
        "list": "technician.view",
        "retrieve": "technician.view",
        "create": "technician.create",
        "update": "technician.update",
        "partial_update": "technician.update",
    }

    def get_queryset(self):
        queryset = Technician.objects.select_related("user", "user__role").prefetch_related(
            "skills__skill",
            "certifications",
        )
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(employee_number__icontains=search)
                | Q(user__full_name__icontains=search)
                | Q(user__email__icontains=search)
            )
        return queryset.order_by("employee_number")

    def create(self, request, *args, **kwargs):
        serializer = TechnicianWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        technician = TechnicianService.create(actor=request.user, data=serializer.validated_data)
        data = TechnicianSerializer(technician).data
        return Response({"success": True, "data": data}, status=201)

    def partial_update(self, request, *args, **kwargs):
        technician = self.get_object()
        serializer = TechnicianWriteSerializer(instance=technician, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        technician = TechnicianService.update(
            actor=request.user,
            technician=technician,
            data=serializer.validated_data,
        )
        data = TechnicianSerializer(technician).data
        return Response({"success": True, "data": data})


class SkillViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "skill.view",
        "retrieve": "skill.view",
        "create": "skill.create",
        "update": "skill.update",
        "partial_update": "skill.update",
        "destroy": "skill.delete",
    }

    def get_queryset(self):
        queryset = Skill.objects.all()
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(code__icontains=search))
        return queryset.order_by("code")

    def perform_create(self, serializer):
        skill = SkillService.create(actor=self.request.user, data=serializer.validated_data)
        serializer.instance = skill

    def perform_update(self, serializer):
        skill = SkillService.update(
            actor=self.request.user,
            skill=serializer.instance,
            data=serializer.validated_data,
        )
        serializer.instance = skill


class TechnicianSkillViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = TechnicianSkillSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "technician.view",
        "retrieve": "technician.view",
        "create": "technician.update",
        "update": "technician.update",
        "partial_update": "technician.update",
        "destroy": "technician.update",
    }

    def get_technician(self) -> Technician:
        return get_object_or_404(Technician, pk=self.kwargs["technician_id"])

    def get_queryset(self):
        return TechnicianSkill.objects.filter(
            technician_id=self.kwargs["technician_id"]
        ).select_related("skill").order_by("skill__code")

    def perform_create(self, serializer):
        row = TechnicianCapabilityService.add_skill(
            actor=self.request.user,
            technician=self.get_technician(),
            data=serializer.validated_data,
        )
        serializer.instance = row

    def perform_update(self, serializer):
        row = TechnicianCapabilityService.update_skill(
            actor=self.request.user,
            row=serializer.instance,
            data=serializer.validated_data,
        )
        serializer.instance = row


class TechnicianCertificationViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = TechnicianCertificationSerializer
    permission_classes = [HasPermissionCode]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "technician.view",
        "retrieve": "technician.view",
        "create": "technician.update",
        "update": "technician.update",
        "partial_update": "technician.update",
        "destroy": "technician.update",
    }

    def get_technician(self) -> Technician:
        return get_object_or_404(Technician, pk=self.kwargs["technician_id"])

    def get_queryset(self):
        return TechnicianCertification.objects.filter(
            technician_id=self.kwargs["technician_id"]
        ).order_by("-issued_at", "name")

    def perform_create(self, serializer):
        cert = TechnicianCapabilityService.add_certification(
            actor=self.request.user,
            technician=self.get_technician(),
            data=serializer.validated_data,
        )
        serializer.instance = cert

    def perform_update(self, serializer):
        cert = TechnicianCapabilityService.update_certification(
            actor=self.request.user,
            cert=serializer.instance,
            data=serializer.validated_data,
        )
        serializer.instance = cert
