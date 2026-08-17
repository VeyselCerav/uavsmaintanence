from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand

from apps.accounts.models import Role, User
from apps.technicians.enums import TechnicianStatus
from apps.technicians.models import Skill, Technician, TechnicianCertification, TechnicianSkill


class Command(BaseCommand):
    help = "Create a local ADMIN user and demo technician if missing. Development only."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="admin@local.test")
        parser.add_argument("--password", default="admin12345")
        parser.add_argument("--name", default="System Admin")

    def handle(self, *args, **options):
        role = Role.objects.filter(code="ADMIN").first()
        if role is None:
            self.stderr.write("Run seed_rbac first.")
            return
        user, created = User.objects.get_or_create(
            email=options["email"],
            defaults={
                "full_name": options["name"],
                "role": role,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        user.set_password(options["password"])
        user.role = role
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created {user.email}"))
        else:
            self.stdout.write(self.style.WARNING(f"Updated {user.email}"))
        self._seed_technician()

    def _seed_technician(self):
        tech_role = Role.objects.filter(code="TECHNICIAN").first()
        if tech_role is None:
            return
        tech_user, _ = User.objects.get_or_create(
            email="tech@local.test",
            defaults={
                "full_name": "Demo Technician",
                "role": tech_role,
                "is_active": True,
            },
        )
        tech_user.role = tech_role
        tech_user.is_active = True
        tech_user.set_password("tech12345")
        tech_user.save()
        Technician.objects.update_or_create(
            user=tech_user,
            defaults={
                "employee_number": "EMP-001",
                "status": TechnicianStatus.ACTIVE,
                "is_demo": True,
                "notes": "DEMO DATA — resmi bakım standardı değildir.",
            },
        )
        self._seed_skills(tech_user)
        self.stdout.write(self.style.SUCCESS("Technician profile ready: tech@local.test"))

    def _seed_skills(self, tech_user):
        technician = Technician.objects.filter(user=tech_user).first()
        if technician is None:
            return
        catalog = [
            ("VISUAL", "Görsel muayene"),
            ("AVIONICS", "Aviyonik"),
            ("PROPULSION", "İtki"),
        ]
        skills = {}
        for code, name in catalog:
            skill, _ = Skill.objects.update_or_create(
                code=code,
                defaults={"name": name, "is_demo": True, "is_active": True},
            )
            skills[code] = skill
        TechnicianSkill.objects.update_or_create(
            technician=technician,
            skill=skills["VISUAL"],
            defaults={"certified_at": date(2025, 1, 15), "expires_at": date(2027, 1, 15)},
        )
        TechnicianCertification.objects.update_or_create(
            technician=technician,
            name="Part-66 B1",
            defaults={
                "issuer": "SHGM",
                "issued_at": date(2024, 6, 1),
                "expires_at": date(2027, 6, 1),
                "document_id": "SHGM-P66-B1-DEMO",
            },
        )
