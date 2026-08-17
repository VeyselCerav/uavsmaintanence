from rest_framework.permissions import BasePermission


def user_has_permission(user, code: str) -> bool:
    if not getattr(user, "is_authenticated", False) or getattr(user, "is_deleted", False):
        return False
    role = getattr(user, "role", None)
    if role is None:
        return False
    if role.code == "ADMIN":
        return True
    return role.role_permissions.filter(permission__code=code).exists()


class HasPermissionCode(BasePermission):
    def has_permission(self, request, view):
        permission_map = getattr(view, "permission_map", {})
        code = permission_map.get(getattr(view, "action", None))
        if not code:
            return False
        return user_has_permission(request.user, code)
