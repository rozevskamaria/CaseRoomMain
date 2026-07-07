from __future__ import annotations

import pytest

from app.auth.service import AuthService
from app.auth.stores import (
    InMemoryMagicLinkStore,
    InMemoryRateLimiter,
    InMemorySessionStore,
    InMemoryUserStore,
)
from app.core.config import Settings
from app.services.jobs import InMemoryJobQueue
from app.workers.jobs import SEND_MAGIC_LINK, send_magic_link


class RecordingEmail:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send_magic_link(self, to_email: str, link: str) -> None:
        self.sent.append((to_email, link))


class InlineBackground:
    def __init__(self) -> None:
        self._tasks: list = []

    def __call__(self, coro_factory) -> None:
        self._tasks.append(coro_factory)

    async def drain(self) -> None:
        while self._tasks:
            task = self._tasks.pop(0)
            await task()


def _settings() -> Settings:
    return Settings(PUBLIC_BASE_URL="https://caseroom.test", CONSENT_VERSION="v1")


async def test_send_magic_link_job_calls_email_service():
    email = RecordingEmail()
    await send_magic_link(
        {"email_service": email}, to_email="x@rsu.edu.lv", link="https://l"
    )
    assert email.sent == [("x@rsu.edu.lv", "https://l")]


async def test_inmemory_queue_records_and_runs_inline():
    email = RecordingEmail()
    queue = InMemoryJobQueue({SEND_MAGIC_LINK: send_magic_link})
    await queue.enqueue(SEND_MAGIC_LINK, to_email="y@rsu.edu.lv", link="https://m")
    assert len(queue.jobs) == 1
    assert queue.jobs[0].job_name == SEND_MAGIC_LINK
    assert email.sent == []
    await queue.run_pending({"email_service": email})
    assert email.sent == [("y@rsu.edu.lv", "https://m")]
    assert queue.jobs == []


async def test_auth_service_enqueues_email_via_queue_not_inline():
    users = InMemoryUserStore()
    email = RecordingEmail()
    queue = InMemoryJobQueue({SEND_MAGIC_LINK: send_magic_link})
    bg = InlineBackground()
    service = AuthService(
        users=users,
        sessions=InMemorySessionStore(),
        links=InMemoryMagicLinkStore(),
        limiter=InMemoryRateLimiter(),
        email=email,
        settings=_settings(),
        background=bg,
        queue=queue,
    )

    await service.register_student("123456", "Test", "1.1.1.1")
    assert queue.jobs == []
    assert email.sent == []

    await bg.drain()
    assert len(queue.jobs) == 1
    assert email.sent == []

    await queue.run_pending({"email_service": email})
    assert len(email.sent) == 1
    assert email.sent[0][0] == "123456@rsu.edu.lv"


async def test_auth_service_create_staff_enqueues_email():
    from app.models.user import UserRole

    users = InMemoryUserStore()
    email = RecordingEmail()
    queue = InMemoryJobQueue({SEND_MAGIC_LINK: send_magic_link})
    bg = InlineBackground()
    service = AuthService(
        users=users,
        sessions=InMemorySessionStore(),
        links=InMemoryMagicLinkStore(),
        limiter=InMemoryRateLimiter(),
        email=email,
        settings=_settings(),
        background=bg,
        queue=queue,
    )

    await service.create_staff(
        "tutor1", "tutor1@rsu.edu.lv", "Tutor One", UserRole.staff
    )
    await bg.drain()
    assert len(queue.jobs) == 1
    await queue.run_pending({"email_service": email})
    assert email.sent[-1][0] == "tutor1@rsu.edu.lv"


async def test_worker_settings_only_arq_importer():
    import app.services.jobs as jobs_seam
    import app.workers.jobs as job_funcs

    assert "arq" not in [m for m in dir(jobs_seam)]
    assert "arq" not in [m for m in dir(job_funcs)]

    from app.workers.worker import WorkerSettings

    names = {fn.__name__ for fn in WorkerSettings.functions}
    assert names == {"send_magic_link", "generate_research_export"}


def test_only_worker_module_imports_arq():
    import ast
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "app"
    offenders = []
    for path in root.rglob("*.py"):
        if path.name == "worker.py" and path.parent.name == "workers":
            continue
        if path.name == "queue.py" and path.parent.name == "workers":
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] == "arq":
                        offenders.append(str(path))
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "").split(".")[0] == "arq":
                    offenders.append(str(path))
    assert offenders == [], f"unexpected arq imports: {offenders}"


@pytest.mark.parametrize("missing", ["arq import is lazy in queue.create_arq_pool"])
def test_queue_create_arq_pool_is_lazy(missing):
    import ast
    from pathlib import Path

    src = (
        Path(__file__).resolve().parent.parent / "app" / "workers" / "queue.py"
    ).read_text()
    tree = ast.parse(src)
    module_level_arq = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "arq"
        ):
            module_level_arq.append(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("arq"):
                    module_level_arq.append(alias.name)
    assert module_level_arq == []
