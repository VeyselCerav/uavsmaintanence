from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import PasswordResetToken, User
from apps.audit.enums import AuditAction
from apps.audit.services import AuditService
from apps.core.api_exceptions import (
    InvalidCurrentPassword,
    InvalidLocale,
    InvalidNewPassword,
    InvalidResetToken,
)


class AuthService:
    @staticmethod
    def issue_tokens(user: User) -> dict:
        refresh = RefreshToken.for_user(user)
        user.mark_login()
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "locale": user.locale,
                "role": user.role.code if user.role else None,
                "permissions": list(
                    user.role.role_permissions.values_list("permission__code", flat=True)
                    if user.role_id
                    else []
                ),
            },
        }

    @staticmethod
    def logout(refresh_token: str) -> None:
        token = RefreshToken(refresh_token)
        token.blacklist()

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def request_password_reset(cls, *, email: str) -> dict:
        payload = {"accepted": True}
        user = User.objects.filter(
            email__iexact=email.strip(),
            is_active=True,
            is_deleted=False,
        ).first()
        if user is None:
            return payload
        PasswordResetToken.objects.filter(user=user, used_at__isnull=True).update(
            used_at=timezone.now()
        )
        raw = secrets.token_urlsafe(32)
        PasswordResetToken.objects.create(
            user=user,
            token_hash=cls._hash_token(raw),
            expires_at=timezone.now() + timedelta(hours=settings.PASSWORD_RESET_HOURS),
        )
        if settings.DEBUG:
            payload["reset_token"] = raw
        return payload

    @classmethod
    def confirm_password_reset(cls, *, token: str, new_password: str) -> None:
        hashed = cls._hash_token(token)
        record = (
            PasswordResetToken.objects.select_related("user")
            .filter(token_hash=hashed, used_at__isnull=True, expires_at__gt=timezone.now())
            .first()
        )
        if record is None:
            raise InvalidResetToken()
        user = record.user
        if not user.is_active or user.is_deleted:
            raise InvalidResetToken()
        try:
            validate_password(new_password, user)
        except DjangoValidationError as exc:
            raise InvalidNewPassword() from exc
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
        record.used_at = timezone.now()
        record.save(update_fields=["used_at"])
        PasswordResetToken.objects.filter(user=user, used_at__isnull=True).update(
            used_at=timezone.now()
        )


class ProfileService:
    @classmethod
    def update(cls, *, user: User, data: dict, request=None) -> User:
        old = {"full_name": user.full_name, "locale": user.locale, "timezone": user.timezone}
        if "full_name" in data and data["full_name"]:
            user.full_name = data["full_name"].strip()
        if "locale" in data and data["locale"]:
            locale = data["locale"]
            if locale not in settings.AUTH_LOCALE_CHOICES:
                raise InvalidLocale()
            user.locale = locale
        if "timezone" in data and data["timezone"]:
            user.timezone = data["timezone"]
        new_password = data.get("new_password")
        if new_password:
            current = data.get("current_password") or ""
            if not user.check_password(current):
                raise InvalidCurrentPassword()
            try:
                validate_password(new_password, user)
            except DjangoValidationError as exc:
                raise InvalidNewPassword() from exc
            user.set_password(new_password)
        user.save()
        AuditService.log(
            actor=user,
            action=AuditAction.UPDATE,
            entity_type="User",
            entity_id=user.id,
            old_value=old,
            new_value={
                "full_name": user.full_name,
                "locale": user.locale,
                "timezone": user.timezone,
            },
            message="profile",
            request=request,
        )
        return user
