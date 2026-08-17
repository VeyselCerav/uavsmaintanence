from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import EnvelopeMixin
from apps.core.permissions import HasPermissionCode
from apps.flights.models import Flight
from apps.flights.serializers import FlightSerializer
from apps.flights.services import FlightService


class FlightAccessPermission(HasPermissionCode):
    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return False
        role = getattr(getattr(request.user, "role", None), "code", "")
        if role in {"ADMIN", "MAINTENANCE_MANAGER"}:
            return True
        if role == "OPERATOR":
            if obj.operator_id != request.user.id:
                return False
            if view.action in {"update", "partial_update", "destroy"} and obj.counters_applied:
                return False
            return True
        return view.action in {"retrieve", "list"}


class FlightViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    serializer_class = FlightSerializer
    permission_classes = [FlightAccessPermission]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_map = {
        "list": "flight.view",
        "retrieve": "flight.view",
        "create": "flight.create",
        "update": "flight.update",
        "partial_update": "flight.update",
        "destroy": "flight.delete",
        "complete": "flight.complete",
    }

    def get_queryset(self):
        queryset = Flight.objects.select_related("uav", "operator", "mission_type")
        role = getattr(getattr(self.request.user, "role", None), "code", "")
        if role == "OPERATOR":
            queryset = queryset.filter(operator=self.request.user)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(flight_number__icontains=search) | Q(uav__registration_number__icontains=search)
            )
        uav_id = self.request.query_params.get("uav")
        if uav_id:
            queryset = queryset.filter(uav_id=uav_id)
        return queryset.order_by("-start_at")

    def perform_create(self, serializer):
        flight = FlightService.create(
            actor=self.request.user,
            validated_data=serializer.validated_data,
        )
        serializer.instance = FlightService.with_relations(flight)

    def perform_update(self, serializer):
        flight = FlightService.update(
            actor=self.request.user,
            flight=serializer.instance,
            validated_data=serializer.validated_data,
        )
        serializer.instance = FlightService.with_relations(flight)

    def perform_destroy(self, instance):
        if instance.counters_applied:
            from apps.core.api_exceptions import FlightCountersAlreadyApplied

            raise FlightCountersAlreadyApplied()
        instance.delete()

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        flight = FlightService.complete(actor=request.user, flight=self.get_object())
        data = FlightSerializer(flight).data
        return Response({"success": True, "data": data})
