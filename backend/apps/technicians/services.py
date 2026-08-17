from __future__ import annotations

from django.db import IntegrityError

from apps.accounts.models import Role, User
from apps.core.api_exceptions import (
    InvalidCertificationDates,
    SkillCodeTaken,
    TechnicianEmailTaken,
    TechnicianProfileExists,
    TechnicianSkillExists,
)
from apps.technicians.enums import TechnicianStatus
from apps.technicians.models import Skill, Technician, TechnicianCertification, TechnicianSkill


def _validate_date_range(start, end) -> None:
    if start and end and end < start:
        raise InvalidCertificationDates()


class TechnicianService:
    @staticmethod
    def with_user(technician: Technician) -> Technician:
        return Technician.objects.select_related("user", "user__role").prefetch_related(
            "skills__skill",
            "certifications",
        ).get(pk=technician.pk)

    @classmethod
    def create(cls, *, actor, data: dict) -> Technician:
        user = data.get("user")
        if user is None:
            email = data["email"].strip().lower()
            full_name = data["full_name"].strip()
            password = data["password"]
            if User.objects.filter(email__iexact=email).exists():
                raise TechnicianEmailTaken()
            role = Role.objects.get(code="TECHNICIAN")
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role=role,
                is_active=True,
            )
        elif Technician.objects.filter(user=user).exists():
            raise TechnicianProfileExists()
        technician = Technician(
            user=user,
            employee_number=data["employee_number"],
            status=data.get("status") or TechnicianStatus.ACTIVE,
            notes=data.get("notes") or "",
            is_demo=bool(data.get("is_demo", False)),
            created_by=actor,
            updated_by=actor,
        )
        technician.save()
        return cls.with_user(technician)

    @classmethod
    def update(cls, *, actor, technician: Technician, data: dict) -> Technician:
        if "employee_number" in data:
            technician.employee_number = data["employee_number"]
        if "status" in data:
            technician.status = data["status"]
        if "notes" in data:
            technician.notes = data["notes"]
        user = technician.user
        if data.get("full_name"):
            user.full_name = data["full_name"]
        if data.get("email"):
            email = data["email"].strip().lower()
            if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                raise TechnicianEmailTaken()
            user.email = email
        if data.get("password"):
            user.set_password(data["password"])
        user.save()
        technician.updated_by = actor
        technician.save()
        return cls.with_user(technician)


class SkillService:
    @classmethod
    def create(cls, *, actor, data: dict) -> Skill:
        code = data["code"].strip()
        if Skill.objects.filter(code=code).exists():
            raise SkillCodeTaken()
        skill = Skill(
            code=code,
            name=data["name"].strip(),
            description=data.get("description") or "",
            is_active=data.get("is_active", True),
            is_demo=bool(data.get("is_demo", False)),
            created_by=actor,
            updated_by=actor,
        )
        try:
            skill.save()
        except IntegrityError as exc:
            raise SkillCodeTaken() from exc
        return skill

    @classmethod
    def update(cls, *, actor, skill: Skill, data: dict) -> Skill:
        if "code" in data:
            code = data["code"].strip()
            if Skill.objects.filter(code=code).exclude(pk=skill.pk).exists():
                raise SkillCodeTaken()
            skill.code = code
        if "name" in data:
            skill.name = data["name"].strip()
        if "description" in data:
            skill.description = data["description"]
        if "is_active" in data:
            skill.is_active = data["is_active"]
        skill.updated_by = actor
        try:
            skill.save()
        except IntegrityError as exc:
            raise SkillCodeTaken() from exc
        return skill


class TechnicianCapabilityService:
    @classmethod
    def add_skill(cls, *, actor, technician: Technician, data: dict) -> TechnicianSkill:
        _validate_date_range(data.get("certified_at"), data.get("expires_at"))
        skill = data["skill"]
        if TechnicianSkill.objects.filter(technician=technician, skill=skill).exists():
            raise TechnicianSkillExists()
        row = TechnicianSkill(
            technician=technician,
            skill=skill,
            certified_at=data.get("certified_at"),
            expires_at=data.get("expires_at"),
            created_by=actor,
            updated_by=actor,
        )
        try:
            row.save()
        except IntegrityError as exc:
            raise TechnicianSkillExists() from exc
        return TechnicianSkill.objects.select_related("skill").get(pk=row.pk)

    @classmethod
    def update_skill(cls, *, actor, row: TechnicianSkill, data: dict) -> TechnicianSkill:
        certified_at = data.get("certified_at", row.certified_at)
        expires_at = data.get("expires_at", row.expires_at)
        _validate_date_range(certified_at, expires_at)
        if "certified_at" in data:
            row.certified_at = data["certified_at"]
        if "expires_at" in data:
            row.expires_at = data["expires_at"]
        row.updated_by = actor
        row.save()
        return TechnicianSkill.objects.select_related("skill").get(pk=row.pk)

    @classmethod
    def add_certification(cls, *, actor, technician: Technician, data: dict) -> TechnicianCertification:
        _validate_date_range(data.get("issued_at"), data.get("expires_at"))
        cert = TechnicianCertification(
            technician=technician,
            name=data["name"].strip(),
            issuer=data["issuer"].strip(),
            issued_at=data.get("issued_at"),
            expires_at=data.get("expires_at"),
            document_id=(data.get("document_id") or "").strip(),
            created_by=actor,
            updated_by=actor,
        )
        cert.save()
        return cert

    @classmethod
    def update_certification(
        cls, *, actor, cert: TechnicianCertification, data: dict
    ) -> TechnicianCertification:
        issued_at = data.get("issued_at", cert.issued_at)
        expires_at = data.get("expires_at", cert.expires_at)
        _validate_date_range(issued_at, expires_at)
        if "name" in data:
            cert.name = data["name"].strip()
        if "issuer" in data:
            cert.issuer = data["issuer"].strip()
        if "issued_at" in data:
            cert.issued_at = data["issued_at"]
        if "expires_at" in data:
            cert.expires_at = data["expires_at"]
        if "document_id" in data:
            cert.document_id = (data.get("document_id") or "").strip()
        cert.updated_by = actor
        cert.save()
        return cert
