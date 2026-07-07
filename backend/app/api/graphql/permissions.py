from __future__ import annotations

from typing import Any

from strawberry.permission import BasePermission

from app.models.user import UserRole, UserStatus


def active_user(info: Any):
    user = getattr(info.context, "current_user", None)
    if user is None or user.status != UserStatus.active:
        return None
    return user


class IsAuthenticated(BasePermission):
    message = "Authentication required"

    def has_permission(self, source: Any, info: Any, **kwargs: Any) -> bool:
        return active_user(info) is not None


class IsAdmin(BasePermission):
    message = "Admin only"

    def has_permission(self, source: Any, info: Any, **kwargs: Any) -> bool:
        user = active_user(info)
        return user is not None and user.role == UserRole.admin


class IsStaffOrAdmin(BasePermission):
    message = "Staff or admin only"

    def has_permission(self, source: Any, info: Any, **kwargs: Any) -> bool:
        user = active_user(info)
        return user is not None and user.role in (UserRole.staff, UserRole.admin)
