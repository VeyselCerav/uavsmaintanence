from apps.maintenance.services import MaintenanceDueService, TemplateResolveService
from apps.uavs.models import UAV


class UAVService:
    @staticmethod
    def with_relations(uav: UAV) -> UAV:
        return UAV.objects.select_related(
            "uav_class",
            "platform_type",
            "mission_type",
            "maintenance_template",
        ).get(pk=uav.pk)

    @staticmethod
    def bind_template(uav: UAV) -> UAV:
        template = TemplateResolveService.resolve(
            uav.uav_class_id,
            uav.platform_type_id,
            uav.mission_type_id,
            uav.maintenance_approach,
        )
        uav.maintenance_template = template
        return uav

    @classmethod
    def create(cls, *, actor, validated_data: dict) -> UAV:
        uav = UAV(**validated_data)
        cls.bind_template(uav)
        uav.created_by = actor
        uav.updated_by = actor
        uav.save()
        MaintenanceDueService.recalculate(uav)
        return uav

    @classmethod
    def update(cls, *, actor, uav: UAV, validated_data: dict) -> UAV:
        for field, value in validated_data.items():
            setattr(uav, field, value)
        cls.bind_template(uav)
        uav.updated_by = actor
        uav.save()
        MaintenanceDueService.recalculate(uav)
        return uav
