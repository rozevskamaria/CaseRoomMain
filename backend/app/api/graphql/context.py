from __future__ import annotations

from collections.abc import AsyncIterator

from starlette.requests import Request
from starlette.responses import Response
from strawberry.fastapi import BaseContext

from app.api import runtime
from app.api.graphql.loaders import (
    make_assignments_by_cohort_loader,
    make_attempts_by_student_loader,
    make_cohort_loader,
    make_cohorts_for_user_loader,
    make_events_loader,
    make_staff_by_cohort_loader,
    make_students_by_cohort_loader,
)
from app.auth import runtime as auth_runtime
from app.core.config import get_settings
from app.core.db import get_sessionmaker


class GraphQLContext(BaseContext):
    def __init__(self) -> None:
        super().__init__()
        self.events_loader = make_events_loader()
        self.cohorts_for_user_loader = make_cohorts_for_user_loader()
        self.cohort_loader = make_cohort_loader()
        self.students_by_cohort_loader = make_students_by_cohort_loader()
        self.staff_by_cohort_loader = make_staff_by_cohort_loader()
        self.assignments_by_cohort_loader = make_assignments_by_cohort_loader()
        self.attempts_by_student_loader = make_attempts_by_student_loader()
        self.current_user = None
        self.db_session = None


def _cookie_sid(request: Request | None) -> str | None:
    if request is None:
        return None
    return request.cookies.get(get_settings().SESSION_COOKIE_NAME)


async def get_context(
    request: Request, response: Response
) -> AsyncIterator[GraphQLContext]:
    ctx = GraphQLContext()
    ctx.request = request
    ctx.response = response
    sid = _cookie_sid(request)

    if not runtime.has_service_factory():
        ctx.current_user = await auth_runtime.resolve_current_user(sid, None)
        user_token = auth_runtime.set_request_user(ctx.current_user)
        try:
            yield ctx
        finally:
            auth_runtime.reset_request_user(user_token)
        return

    async with get_sessionmaker()() as session:
        ctx.db_session = session
        service = runtime.build_request_service(session)
        token = runtime.use_request_service(service)
        cohort_service = runtime.build_request_cohort_service(session)
        cohort_token = runtime.use_request_cohort_service(cohort_service)
        authoring_service = runtime.build_request_authoring_service(session)
        authoring_token = runtime.use_request_authoring_service(authoring_service)
        analytics_service = runtime.build_request_analytics_service(session)
        analytics_token = runtime.use_request_analytics_service(analytics_service)
        ctx.current_user = await auth_runtime.resolve_current_user(sid, session)
        user_token = auth_runtime.set_request_user(ctx.current_user)
        try:
            yield ctx
            await session.commit()
        finally:
            auth_runtime.reset_request_user(user_token)
            runtime.reset_request_analytics_service(analytics_token)
            runtime.reset_request_authoring_service(authoring_token)
            runtime.reset_request_cohort_service(cohort_token)
            runtime.reset_request_service(token)
