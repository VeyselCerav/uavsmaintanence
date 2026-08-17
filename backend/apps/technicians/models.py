from django.db import models
from django.db.models import Q

from apps.core.models import SoftDeleteModel
from apps.technicians.enums import TechnicianStatus


class Technician(SoftDeleteModel):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="technician_profile",
    )
    employee_number = models.CharField(max_length=64)
    status = models.CharField(
        max_length=16,
        choices=TechnicianStatus.choices,
        default=TechnicianStatus.ACTIVE,
    )
    notes = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "technician"
        constraints = [
            models.UniqueConstraint(
                fields=["employee_number"],
                condition=Q(is_deleted=False),
                name="uniq_technician_employee_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.employee_number


class Skill(SoftDeleteModel):
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        db_table = "skill"
        ordering = ("code",)
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=Q(is_deleted=False),
                name="uniq_skill_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.code


class TechnicianSkill(SoftDeleteModel):
    technician = models.ForeignKey(
        Technician,
        on_delete=models.CASCADE,
        related_name="skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.PROTECT,
        related_name="technician_skills",
    )
    certified_at = models.DateField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "technician_skill"
        constraints = [
            models.UniqueConstraint(
                fields=["technician", "skill"],
                condition=Q(is_deleted=False),
                name="uniq_technician_skill_alive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.technician_id}:{self.skill_id}"


class TechnicianCertification(SoftDeleteModel):
    technician = models.ForeignKey(
        Technician,
        on_delete=models.CASCADE,
        related_name="certifications",
    )
    name = models.CharField(max_length=128)
    issuer = models.CharField(max_length=128)
    issued_at = models.DateField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    document_id = models.CharField(max_length=128, blank=True)

    class Meta:
        db_table = "technician_certification"
        ordering = ("-issued_at", "name")

    def __str__(self) -> str:
        return self.name
