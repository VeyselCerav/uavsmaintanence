from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.accounts.models import Permission, Role, RolePermission

PERMISSIONS: list[tuple[str, str, str]] = [
    ("dashboard.view", "dashboard", "view"),
    ("admin.access", "admin", "access"),
    ("uav.view", "uav", "view"),
    ("uav.create", "uav", "create"),
    ("uav.update", "uav", "update"),
    ("uav.delete", "uav", "delete"),
    ("uav_class.view", "uav_class", "view"),
    ("uav_class.create", "uav_class", "create"),
    ("uav_class.update", "uav_class", "update"),
    ("uav_class.delete", "uav_class", "delete"),
    ("platform.view", "platform", "view"),
    ("platform.create", "platform", "create"),
    ("platform.update", "platform", "update"),
    ("platform.delete", "platform", "delete"),
    ("mission.view", "mission", "view"),
    ("mission.create", "mission", "create"),
    ("mission.update", "mission", "update"),
    ("mission.delete", "mission", "delete"),
    ("component.view", "component", "view"),
    ("component.create", "component", "create"),
    ("component.update", "component", "update"),
    ("component.delete", "component", "delete"),
    ("flight.view", "flight", "view"),
    ("flight.create", "flight", "create"),
    ("flight.update", "flight", "update"),
    ("flight.delete", "flight", "delete"),
    ("flight.complete", "flight", "complete"),
    ("maintenance.view", "maintenance", "view"),
    ("maintenance.create", "maintenance", "create"),
    ("maintenance.update", "maintenance", "update"),
    ("maintenance.approve", "maintenance", "approve"),
    ("maintenance_template.view", "maintenance_template", "view"),
    ("maintenance_template.create", "maintenance_template", "create"),
    ("maintenance_template.update", "maintenance_template", "update"),
    ("maintenance_template.delete", "maintenance_template", "delete"),
    ("maintenance_rule.view", "maintenance_rule", "view"),
    ("maintenance_rule.create", "maintenance_rule", "create"),
    ("maintenance_rule.update", "maintenance_rule", "update"),
    ("maintenance_rule.delete", "maintenance_rule", "delete"),
    ("work_order.view", "work_order", "view"),
    ("work_order.create", "work_order", "create"),
    ("work_order.update", "work_order", "update"),
    ("work_order.assign", "work_order", "assign"),
    ("work_order.start", "work_order", "start"),
    ("work_order.complete", "work_order", "complete"),
    ("work_order.cancel", "work_order", "cancel"),
    ("failure.view", "failure", "view"),
    ("failure.create", "failure", "create"),
    ("failure.update", "failure", "update"),
    ("failure.delete", "failure", "delete"),
    ("fmea.view", "fmea", "view"),
    ("fmea.create", "fmea", "create"),
    ("fmea.update", "fmea", "update"),
    ("fmea.approve", "fmea", "approve"),
    ("rcm.view", "rcm", "view"),
    ("rcm.create", "rcm", "create"),
    ("rcm.update", "rcm", "update"),
    ("rcm.approve", "rcm", "approve"),
    ("part.view", "part", "view"),
    ("part.create", "part", "create"),
    ("part.update", "part", "update"),
    ("part.delete", "part", "delete"),
    ("technician.view", "technician", "view"),
    ("technician.create", "technician", "create"),
    ("technician.update", "technician", "update"),
    ("skill.view", "skill", "view"),
    ("skill.create", "skill", "create"),
    ("skill.update", "skill", "update"),
    ("skill.delete", "skill", "delete"),
    ("document.view", "document", "view"),
    ("document.create", "document", "create"),
    ("document.delete", "document", "delete"),
    ("reliability.view", "reliability", "view"),
    ("reports.view", "reports", "view"),
    ("reports.export", "reports", "export"),
    ("cost.view", "cost", "view"),
    ("notification.view", "notification", "view"),
    ("user.view", "user", "view"),
    ("user.create", "user", "create"),
    ("user.update", "user", "update"),
    ("user.delete", "user", "delete"),
    ("role.view", "role", "view"),
    ("role.update", "role", "update"),
    ("permission.view", "permission", "view"),
    ("settings.view", "settings", "view"),
    ("settings.update", "settings", "update"),
    ("audit.view", "audit", "view"),
]

ROLES = [
    ("ADMIN", "Administrator"),
    ("MAINTENANCE_MANAGER", "Maintenance Manager"),
    ("TECHNICIAN", "Technician"),
    ("OPERATOR", "Operator"),
    ("VIEWER", "Viewer"),
]

# ADR-12: manager has admin.access but not user/settings/audit.
MANAGER_CODES = {
    "dashboard.view",
    "admin.access",
    "uav.view",
    "uav.create",
    "uav.update",
    "uav_class.view",
    "uav_class.create",
    "uav_class.update",
    "platform.view",
    "platform.create",
    "platform.update",
    "mission.view",
    "mission.create",
    "mission.update",
    "component.view",
    "component.create",
    "component.update",
    "flight.view",
    "flight.create",
    "flight.update",
    "flight.complete",
    "maintenance.view",
    "maintenance.create",
    "maintenance.update",
    "maintenance.approve",
    "maintenance_template.view",
    "maintenance_template.create",
    "maintenance_template.update",
    "maintenance_template.delete",
    "maintenance_rule.view",
    "maintenance_rule.create",
    "maintenance_rule.update",
    "maintenance_rule.delete",
    "work_order.view",
    "work_order.create",
    "work_order.update",
    "work_order.assign",
    "work_order.start",
    "work_order.complete",
    "work_order.cancel",
    "failure.view",
    "failure.create",
    "failure.update",
    "fmea.view",
    "fmea.create",
    "fmea.update",
    "fmea.approve",
    "rcm.view",
    "rcm.create",
    "rcm.update",
    "rcm.approve",
    "part.view",
    "part.create",
    "part.update",
    "technician.view",
    "technician.create",
    "technician.update",
    "skill.view",
    "skill.create",
    "skill.update",
    "document.view",
    "document.create",
    "reliability.view",
    "reports.view",
    "reports.export",
    "cost.view",
    "notification.view",
}

TECHNICIAN_CODES = {
    "dashboard.view",
    "uav.view",
    "component.view",
    "flight.view",
    "maintenance.view",
    "work_order.view",
    "work_order.start",
    "work_order.complete",
    "failure.view",
    "failure.create",
    "failure.update",
    "fmea.view",
    "rcm.view",
    "part.view",
    "document.view",
    "notification.view",
}

OPERATOR_CODES = {
    "dashboard.view",
    "uav.view",
    "component.view",
    "flight.view",
    "flight.create",
    "flight.update",
    "flight.complete",
    "maintenance.view",
    "work_order.view",
    "failure.view",
    "part.view",
    "notification.view",
}

VIEWER_CODES = {
    "dashboard.view",
    "uav.view",
    "uav_class.view",
    "platform.view",
    "mission.view",
    "component.view",
    "flight.view",
    "maintenance.view",
    "work_order.view",
    "failure.view",
    "fmea.view",
    "rcm.view",
    "part.view",
    "technician.view",
    "skill.view",
    "document.view",
    "reliability.view",
    "reports.view",
    "cost.view",
    "notification.view",
}


class Command(BaseCommand):
    help = "Seed system roles and permissions (idempotent)."

    def handle(self, *args, **options):
        permission_map: dict[str, Permission] = {}
        for code, module, action in PERMISSIONS:
            perm, _ = Permission.objects.get_or_create(
                code=code,
                defaults={"module": module, "action": action},
            )
            permission_map[code] = perm

        role_map: dict[str, Role] = {}
        for code, name in ROLES:
            role, _ = Role.objects.get_or_create(
                code=code,
                defaults={"name": name, "is_system": True},
            )
            role.is_system = True
            role.name = name
            role.save(update_fields=["is_system", "name"])
            role_map[code] = role

        assignments = {
            "ADMIN": set(permission_map),
            "MAINTENANCE_MANAGER": MANAGER_CODES,
            "TECHNICIAN": TECHNICIAN_CODES,
            "OPERATOR": OPERATOR_CODES,
            "VIEWER": VIEWER_CODES,
        }

        for role_code, codes in assignments.items():
            role = role_map[role_code]
            for code in codes:
                RolePermission.objects.get_or_create(role=role, permission=permission_map[code])

        self.stdout.write(self.style.SUCCESS("RBAC seed completed."))
