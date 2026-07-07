from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.user import UserRole, UserStatus
from app.repositories.user_repo import UserRepository


async def ensure_admin(session: AsyncSession, settings: Settings) -> None:
    if not settings.admin_logins_list:
        return
    repo = UserRepository(session)
    for login in settings.admin_logins_list:
        existing = await repo.get_by_login_hash(login)
        if existing is not None:
            continue
        email = settings.CASEROOM_ADMIN_EMAIL or f"{login}@rsu.edu.lv"
        user = await repo.create_staff(login, email, None, UserRole.admin)
        await repo.set_status(user.id, UserStatus.active)
    await session.commit()
