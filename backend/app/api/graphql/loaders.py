from __future__ import annotations

from typing import Any

from strawberry.dataloader import DataLoader

from app.api.runtime import get_cohort_service, get_session_service


async def _load_events(keys: list[str]) -> list[list[Any]]:
    resolved = await get_session_service().events_many(list(keys))
    return [resolved.get(key, []) for key in keys]


def make_events_loader() -> DataLoader[str, list[Any]]:
    return DataLoader(load_fn=_load_events)


def make_cohort_loader() -> DataLoader[str, Any]:
    async def _load(keys: list[str]) -> list[Any]:
        resolved = await get_cohort_service().cohorts_by_id(keys)
        return [resolved.get(key) for key in keys]

    return DataLoader(load_fn=_load)


def make_cohorts_for_user_loader() -> DataLoader[tuple[str, bool], list[Any]]:
    async def _load(keys: list[tuple[str, bool]]) -> list[list[Any]]:
        service = get_cohort_service()
        admin_ids = [user_id for user_id, is_admin in keys if is_admin]
        staff_ids = [user_id for user_id, is_admin in keys if not is_admin]
        resolved: dict[str, list[Any]] = {}
        if admin_ids:
            resolved.update(await service.cohorts_for_users(admin_ids, admin=True))
        if staff_ids:
            resolved.update(await service.cohorts_for_users(staff_ids, admin=False))
        return [resolved.get(user_id, []) for user_id, _ in keys]

    return DataLoader(load_fn=_load)


def make_students_by_cohort_loader() -> DataLoader[str, list[Any]]:
    async def _load(keys: list[str]) -> list[list[Any]]:
        resolved = await get_cohort_service().students_for_cohorts(keys)
        return [resolved.get(key, []) for key in keys]

    return DataLoader(load_fn=_load)


def make_staff_by_cohort_loader() -> DataLoader[str, list[Any]]:
    async def _load(keys: list[str]) -> list[list[Any]]:
        resolved = await get_cohort_service().staff_for_cohorts(keys)
        return [resolved.get(key, []) for key in keys]

    return DataLoader(load_fn=_load)


def make_assignments_by_cohort_loader() -> DataLoader[str, list[Any]]:
    async def _load(keys: list[str]) -> list[list[Any]]:
        resolved = await get_cohort_service().assignments_for_cohorts(keys)
        return [resolved.get(key, []) for key in keys]

    return DataLoader(load_fn=_load)


def make_attempts_by_student_loader() -> DataLoader[tuple[str, str], list[Any]]:
    async def _load(keys: list[tuple[str, str]]) -> list[list[Any]]:
        resolved = await get_cohort_service().attempts_for_students(list(keys))
        return [resolved.get(key, []) for key in keys]

    return DataLoader(load_fn=_load)
