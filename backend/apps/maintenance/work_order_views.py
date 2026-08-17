from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode
from apps.maintenance.enums import OPEN_WORK_ORDER_STATUSES
from apps.maintenance.models import MaintenanceDue, WorkOrder
from apps.maintenance.serializers import WorkOrderSerializer
from apps.maintenance.work_order_services import WorkOrderService
from apps.technicians.enums import TechnicianStatus
from apps.technicians.models import Technician


class WorkOrderAccessPermission(HasPermissionCode):
    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return False
        role = getattr(getattr(request.user, "role", None), "code", "")
        if role in {"ADMIN", "MAINTENANCE_MANAGER"}:
            return True
        if role == "TECHNICIAN":
            assigned_user_id = getattr(obj.assigned_technician, "user_id", None)
            if assigned_user_id != request.user.id:
                return False
            return view.action in {"retrieve", "list", "start", "complete", "waiting_parts"}
        return view.action in {"retrieve", "list"}


class WorkOrderViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = WorkOrderSerializer
    permission_classes = [WorkOrderAccessPermission]
    http_method_names = ["get", "post", "patch", "head", "options"]
    permission_map = {
        "list": "work_order.view",
        "retrieve": "work_order.view",
        "create": "work_order.create",
        "update": "work_order.update",
        "partial_update": "work_order.update",
        "assign": "work_order.assign",
        "start": "work_order.start",
        "waiting_parts": "work_order.update",
        "complete": "work_order.complete",
        "cancel": "work_order.cancel",
        "assignees": "work_order.assign",
    }

    def get_queryset(self):
        queryset = WorkOrder.objects.select_related(
            "uav",
            "component",
            "component__component_type",
            "template_item",
            "assigned_technician",
            "assigned_technician__user",
        )
        role = getattr(getattr(self.request.user, "role", None), "code", "")
        if role == "TECHNICIAN":
            queryset = queryset.filter(assigned_technician__user=self.request.user)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) | Q(uav__registration_number__icontains=search)
            )
        uav_id = self.request.query_params.get("uav")
        if uav_id:
            queryset = queryset.filter(uav_id=uav_id)
        status_value = self.request.query_params.get("status")
        if status_value == "open":
            queryset = queryset.filter(status__in=OPEN_WORK_ORDER_STATUSES)
        elif status_value:
            queryset = queryset.filter(status=status_value)
        return queryset.order_by("-created_at")

    def create(self, request, *args, **kwargs):
        due_id = request.data.get("due")
        if due_id:
            due = get_object_or_404(
                MaintenanceDue.objects.select_related("uav", "component", "template_item"),
                pk=due_id,
            )
            work_order = WorkOrderService.create_from_due(actor=request.user, due=due)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            payload = dict(serializer.validated_data)
            payload.pop("due", None)
            work_order = WorkOrderService.create(actor=request.user, validated_data=payload)
        data = WorkOrderSerializer(WorkOrderService.with_relations(work_order)).data
        return Response({"success": True, "data": data}, status=201)

    def _respond(self, work_order: WorkOrder):
        data = WorkOrderSerializer(WorkOrderService.with_relations(work_order)).data
        return Response({"success": True, "data": data})

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        technician_id = request.data.get("assigned_technician")
        technician = get_object_or_404(
            Technician.objects.select_related("user"),
            pk=technician_id,
        )
        work_order = WorkOrderService.assign(
            actor=request.user,
            work_order=self.get_object(),
            technician=technician,
        )
        return self._respond(work_order)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        from apps.maintenance.enums import WorkOrderStatus

        work_order = WorkOrderService.transition(
            actor=request.user,
            work_order=self.get_object(),
            target=WorkOrderStatus.IN_PROGRESS,
        )
        return self._respond(work_order)

    @action(detail=True, methods=["post"], url_path="waiting-parts")
    def waiting_parts(self, request, pk=None):
        from apps.maintenance.enums import WorkOrderStatus

        work_order = WorkOrderService.transition(
            actor=request.user,
            work_order=self.get_object(),
            target=WorkOrderStatus.WAITING_PARTS,
        )
        return self._respond(work_order)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        from apps.maintenance.enums import WorkOrderStatus

        work_order = self.get_object()
        findings = request.data.get("findings")
        if findings:
            work_order.findings = findings
            work_order.save(update_fields=["findings", "updated_at"])
        work_order = WorkOrderService.transition(
            actor=request.user,
            work_order=work_order,
            target=WorkOrderStatus.COMPLETED,
        )
        return self._respond(work_order)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        from apps.maintenance.enums import WorkOrderStatus

        work_order = WorkOrderService.transition(
            actor=request.user,
            work_order=self.get_object(),
            target=WorkOrderStatus.CANCELLED,
        )
        return self._respond(work_order)

    @action(detail=False, methods=["get"])
    def assignees(self, request):
        technicians = (
            Technician.objects.filter(
                status=TechnicianStatus.ACTIVE,
                user__is_active=True,
            )
            .select_related("user", "user__role")
            .order_by("user__full_name")
        )
        data = [
            {
                "id": str(item.id),
                "user_id": str(item.user_id),
                "full_name": item.user.full_name,
                "email": item.user.email,
                "employee_number": item.employee_number,
                "role": item.user.role.code if item.user.role else None,
            }
            for item in technicians
        ]
        return Response({"success": True, "data": data})
