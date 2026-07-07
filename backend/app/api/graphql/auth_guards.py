from __future__ import annotations

from typing import Any

from strawberry.exceptions import StrawberryGraphQLError

from app.api import runtime
from app.api.graphql.permissions import active_user
from app.api.runtime import get_session_service
from app.models.user import UserRole


class AuthError(StrawberryGraphQLError):
    pass


def _forbidden() -> AuthError:
    return AuthError("Forbidden")


def _unauthenticated() -> AuthError:
    return AuthError("Authentication required")


async def require_attempt_access(info: Any, attempt_id: str, *, write: bool) -> None:
    user = active_user(info)
    if user is None:
        raise _unauthenticated()
    if user.role == UserRole.admin:
        return
    owner_id = await get_session_service().get_attempt_owner(attempt_id)
    if owner_id is not None and str(owner_id) == str(user.id):
        return
    if (
        user.role == UserRole.staff
        and not write
        and runtime.has_request_cohort_service()
        and await runtime.get_cohort_service().staff_can_read_attempt(
            str(user.id), attempt_id
        )
    ):
        return
    raise _forbidden()


async def require_cohort_access(info: Any, cohort_id: str, *, write: bool) -> None:
    user = active_user(info)
    if user is None:
        raise _unauthenticated()
    if user.role == UserRole.admin:
        return
    if (
        user.role == UserRole.staff
        and runtime.has_request_cohort_service()
        and await runtime.get_cohort_service().staff_teaches_cohort(
            str(user.id), cohort_id
        )
    ):
        return
    raise _forbidden()


def require_case_authoring_access(info: Any) -> None:
    user = active_user(info)
    if user is None:
        raise _unauthenticated()
    if user.role in (UserRole.staff, UserRole.admin):
        return
    raise _forbidden()
