from __future__ import annotations

from django.utils import timezone

from apps.accounts.models import Role, User
from apps.audit.enums import AuditAction
from apps.audit.services import AuditService
from apps.core.api_exceptions import LastAdminRequired, UserEmailTaken


def _snapshot(user: User) -> dict:
    return {
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.code if user.role_id else None,
        "is_active": user.is_active,
        "locale": user.locale,
    }


class UserService:
    @staticmethod
    def alive():
        return User.objects.filter(is_deleted=False).select_related("role")

    @staticmethod
    def active_admin_count() -> int:
        return User.objects.filter(
            is_deleted=False,
            is_active=True,
            role__code="ADMIN",
        ).count()

    @classmethod
    def ensure_not_last_admin(cls, user: User, *, removing: bool) -> None:
        if not removing:
            return
        if not user.role_id or user.role.code != "ADMIN":
            return
        if not user.is_active or user.is_deleted:
            return
        if cls.active_admin_count() <= 1:
            raise LastAdminRequired()

    @classmethod
    def create(cls, *, actor, data: dict, request=None) -> User:
        email = data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise UserEmailTaken()
        role = data["role"]
        user = User.objects.create_user(
            email=email,
            password=data["password"],
            full_name=data["full_name"].strip(),
            role=role,
            locale=data.get("locale") or "tr",
            timezone=data.get("timezone") or "Europe/Istanbul",
            is_active=data.get("is_active", True),
            is_staff=bool(role and role.code == "ADMIN"),
        )
        AuditService.log(
            actor=actor,
            action=AuditAction.CREATE,
            entity_type="User",
            entity_id=user.id,
            new_value=_snapshot(user),
            request=request,
        )
        return user

    @classmethod
    def update(cls, *, actor, user: User, data: dict, request=None) -> User:
        old = _snapshot(user)
        if "email" in data and data["email"]:
            email = data["email"].strip().lower()
            if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                raise UserEmailTaken()
            user.email = email
        if "full_name" in data and data["full_name"] is not None:
            user.full_name = data["full_name"].strip()
        if "locale" in data and data["locale"]:
            user.locale = data["locale"]
        if "timezone" in data and data["timezone"]:
            user.timezone = data["timezone"]
        if "role" in data and data["role"] is not None:
            new_role: Role = data["role"]
            demoting = user.role_id and user.role.code == "ADMIN" and new_role.code != "ADMIN"
            cls.ensure_not_last_admin(user, removing=bool(demoting))
            user.role = new_role
            user.is_staff = new_role.code == "ADMIN"
        if "is_active" in data and data["is_active"] is not None:
            deactivating = user.is_active and data["is_active"] is False
            cls.ensure_not_last_admin(user, removing=deactivating)
            user.is_active = data["is_active"]
        if data.get("password"):
            user.set_password(data["password"])
        user.save()
        AuditService.log(
            actor=actor,
            action=AuditAction.UPDATE,
            entity_type="User",
            entity_id=user.id,
            old_value=old,
            new_value=_snapshot(user),
            request=request,
        )
        return user

    @classmethod
    def delete(cls, *, actor, user: User, request=None) -> None:
        cls.ensure_not_last_admin(user, removing=True)
        old = _snapshot(user)
        user.is_deleted = True
        user.is_active = False
        user.deleted_at = timezone.now()
        user.save(update_fields=["is_deleted", "is_active", "deleted_at", "updated_at"])
        AuditService.log(
            actor=actor,
            action=AuditAction.DELETE,
            entity_type="User",
            entity_id=user.id,
            old_value=old,
            request=request,
        )
