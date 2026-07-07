from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import LLMClient
from app.services import SessionService
from app.services.stores import AttemptStore, CaseSource

if TYPE_CHECKING:
    from app.services.analytics import AnalyticsService
    from app.services.case_authoring_service import CaseAuthoringService
    from app.services.cohort import CohortService

_llm_client: LLMClient | None = None
_session_service: SessionService | None = None
_store_override: AttemptStore | None = None
_cases_override: CaseSource | None = None
_service_factory: Callable[[AsyncSession], SessionService] | None = None
_cohort_service_factory: Callable[[AsyncSession], "CohortService"] | None = None

_request_service: ContextVar[SessionService | None] = ContextVar(
    "request_service", default=None
)
_request_cohort_service: ContextVar["CohortService | None"] = ContextVar(
    "request_cohort_service", default=None
)
_request_authoring_service: ContextVar["CaseAuthoringService | None"] = ContextVar(
    "request_authoring_service", default=None
)
_request_analytics_service: ContextVar["AnalyticsService | None"] = ContextVar(
    "request_analytics_service", default=None
)


def set_llm_client(client: LLMClient) -> None:
    global _llm_client, _session_service
    _llm_client = client
    _session_service = SessionService(
        client, store=_store_override, cases=_cases_override
    )


def set_session_service(service: SessionService) -> None:
    global _session_service
    _session_service = service


def set_stores(store: AttemptStore | None, cases: CaseSource | None) -> None:
    global _store_override, _cases_override, _session_service
    _store_override = store
    _cases_override = cases
    _session_service = None


def set_service_factory(
    factory: Callable[[AsyncSession], SessionService] | None,
) -> None:
    global _service_factory
    _service_factory = factory


def set_cohort_service_factory(
    factory: Callable[[AsyncSession], "CohortService"] | None,
) -> None:
    global _cohort_service_factory
    _cohort_service_factory = factory


def has_service_factory() -> bool:
    return _service_factory is not None


def build_request_service(session: AsyncSession) -> SessionService:
    if _service_factory is None:
        raise RuntimeError("No request service factory registered")
    return _service_factory(session)


def build_request_cohort_service(session: AsyncSession) -> "CohortService":
    from app.repositories.assignment_repo import AssignmentRepository
    from app.repositories.case_repo import CaseRepository
    from app.repositories.cohort_repo import CohortRepository
    from app.services.cohort import CohortService

    if _cohort_service_factory is not None:
        return _cohort_service_factory(session)
    return CohortService(
        CohortRepository(session),
        AssignmentRepository(session),
        CaseRepository(session),
    )


def use_request_service(service: SessionService):
    return _request_service.set(service)


def reset_request_service(token) -> None:
    _request_service.reset(token)


def use_request_cohort_service(service: "CohortService"):
    return _request_cohort_service.set(service)


def reset_request_cohort_service(token) -> None:
    _request_cohort_service.reset(token)


def build_request_authoring_service(session: AsyncSession) -> "CaseAuthoringService":
    from app.repositories.case_authoring_repo import CaseAuthoringRepository
    from app.services.case_authoring_service import CaseAuthoringService

    return CaseAuthoringService(CaseAuthoringRepository(session))


def build_request_analytics_service(session: AsyncSession) -> "AnalyticsService":
    from app.repositories.analytics_repo import AnalyticsRepository
    from app.services.analytics import AnalyticsService

    return AnalyticsService(AnalyticsRepository(session))


def use_request_analytics_service(service: "AnalyticsService"):
    return _request_analytics_service.set(service)


def reset_request_analytics_service(token) -> None:
    _request_analytics_service.reset(token)


def get_analytics_service() -> "AnalyticsService":
    service = _request_analytics_service.get()
    if service is None:
        raise RuntimeError("No request-scoped AnalyticsService available")
    return service


def has_request_analytics_service() -> bool:
    return _request_analytics_service.get() is not None


def use_request_authoring_service(service: "CaseAuthoringService"):
    return _request_authoring_service.set(service)


def reset_request_authoring_service(token) -> None:
    _request_authoring_service.reset(token)


def get_authoring_service() -> "CaseAuthoringService":
    service = _request_authoring_service.get()
    if service is None:
        raise RuntimeError("No request-scoped CaseAuthoringService available")
    return service


def has_request_authoring_service() -> bool:
    return _request_authoring_service.get() is not None


def get_cohort_service() -> "CohortService":
    service = _request_cohort_service.get()
    if service is None:
        raise RuntimeError("No request-scoped CohortService available")
    return service


def has_request_cohort_service() -> bool:
    return _request_cohort_service.get() is not None


def reset() -> None:
    global _llm_client, _session_service, _store_override, _cases_override
    global _service_factory, _cohort_service_factory
    _llm_client = None
    _session_service = None
    _store_override = None
    _cases_override = None
    _service_factory = None
    _cohort_service_factory = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def get_session_service() -> SessionService:
    global _session_service
    request_service = _request_service.get()
    if request_service is not None:
        return request_service
    if _session_service is None:
        _session_service = SessionService(
            get_llm_client(), store=_store_override, cases=_cases_override
        )
    return _session_service
