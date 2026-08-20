from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import runtime
from app.api.graphql import graphql_router
from app.api.sse import router as sse_router
from app.auth import runtime as auth_runtime
from app.core.config import get_settings, validate_production_settings
from app.core.logging import configure_logging
from app.services.stores import build_db_service


def _register_db_backend() -> None:
    def factory(session):
        return build_db_service(session, runtime.get_llm_client())

    runtime.set_service_factory(factory)

    def cohort_factory(session):
        from app.repositories.assignment_repo import AssignmentRepository
        from app.repositories.case_repo import CaseRepository
        from app.repositories.cohort_repo import CohortRepository
        from app.services.cohort import CohortService

        return CohortService(
            CohortRepository(session),
            AssignmentRepository(session),
            CaseRepository(session),
        )

    runtime.set_cohort_service_factory(cohort_factory)


async def _bootstrap_admin() -> None:
    from app.auth.bootstrap import ensure_admin
    from app.core.db import get_sessionmaker

    settings = get_settings()
    if not settings.admin_logins_list:
        return
    async with get_sessionmaker()() as session:
        await ensure_admin(session, settings)


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    validate_production_settings(settings)

    if settings.APP_ENV == "production":
        _register_db_backend()
        auth_runtime.configure_production()
    else:
        auth_runtime.configure_inmemory()

    mcp_app = None
    mcp_server = None
    if settings.MCP_ENABLED:
        from app.core.db import get_sessionmaker
        from app.mcp.mount import build_mcp_app

        mcp_app, mcp_server = build_mcp_app(settings, get_sessionmaker)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        async with AsyncExitStack() as stack:
            if mcp_server is not None:
                from app.mcp.mount import mcp_lifespan

                await stack.enter_async_context(mcp_lifespan(mcp_server))
            if settings.APP_ENV == "production":
                from app.workers.queue import configure_production, create_arq_pool

                pool = await create_arq_pool()
                configure_production(pool)
                await _bootstrap_admin()
            yield

    app = FastAPI(title="CaseRoom Backend", version=__version__, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(graphql_router, prefix="/graphql")

    app.include_router(sse_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    if mcp_app is not None:
        app.mount("/mcp", mcp_app)

    return app


app = create_app()
