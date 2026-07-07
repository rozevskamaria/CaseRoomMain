from __future__ import annotations

import uuid

from sqlalchemy import bindparam, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import User, UserRole, UserStatus


def _key():
    return bindparam(None, get_settings().PGCRYPTO_KEY)


def _pepper():
    return bindparam(None, get_settings().LOGIN_HASH_PEPPER)


def _encrypt(plaintext: str | None):
    if plaintext is None:
        return None
    return func.pgp_sym_encrypt(plaintext, _key())


def _decrypt(cipher):
    return func.pgp_sym_decrypt(cipher, _key())


def _login_hash(login_name: str):
    return func.encode(func.hmac(login_name, _pepper(), "sha256"), "hex")


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _enc(self, plaintext: str | None) -> bytes | None:
        if plaintext is None:
            return None
        return await self._session.scalar(select(_encrypt(plaintext)))

    async def create(
        self,
        login_name: str,
        email: str | None,
        full_name: str | None,
        role: str,
    ) -> User:
        return await self._create(login_name, email, full_name, UserRole(role))

    async def create_student(self, login_name: str, full_name: str | None) -> User:
        email = f"{login_name}@rsu.edu.lv"
        return await self._create(login_name, email, full_name, UserRole.student)

    async def create_staff(
        self,
        login_name: str,
        email: str,
        full_name: str | None,
        role: UserRole,
    ) -> User:
        return await self._create(login_name, email, full_name, role)

    async def _create(
        self,
        login_name: str,
        email: str | None,
        full_name: str | None,
        role: UserRole,
    ) -> User:
        login_hash = await self._session.scalar(select(_login_hash(login_name)))
        user = User(
            login_name=await self._enc(login_name),
            login_name_hash=login_hash,
            email=await self._enc(email),
            full_name=await self._enc(full_name),
            role=role,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def get_by_login_hash(self, login_name: str) -> User | None:
        login_hash = await self._session.scalar(select(_login_hash(login_name)))
        stmt = select(User).where(User.login_name_hash == login_hash)
        return await self._session.scalar(stmt)

    get_by_login_name = get_by_login_hash

    async def get(self, user_id: uuid.UUID | str) -> User | None:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        return await self._session.get(User, user_id)

    async def decrypt_login_name(self, user: User) -> str:
        return await self._session.scalar(select(_decrypt(user.login_name)))

    async def decrypt_email(self, user: User) -> str | None:
        if user.email is None:
            return None
        return await self._session.scalar(select(_decrypt(user.email)))

    async def decrypt_full_name(self, user: User) -> str | None:
        if user.full_name is None:
            return None
        return await self._session.scalar(select(_decrypt(user.full_name)))

    async def set_status(
        self, user_id: uuid.UUID | str, status: UserStatus
    ) -> None:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        await self._session.execute(
            update(User).where(User.id == user_id).values(status=status)
        )
        await self._session.flush()

    async def stamp_consent(
        self, user_id: uuid.UUID | str, version: str
    ) -> None:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(consent_version=version, consent_at=func.now())
        )
        await self._session.flush()


class DbUserStore:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def get(self, user_id: str) -> User | None:
        return await self._repo.get(user_id)

    async def get_by_login_hash(self, login_name: str) -> User | None:
        return await self._repo.get_by_login_hash(login_name)

    async def create_student(self, login_name: str, full_name: str | None) -> User:
        return await self._repo.create_student(login_name, full_name)

    async def create_staff(
        self,
        login_name: str,
        email: str,
        full_name: str | None,
        role: UserRole,
    ) -> User:
        return await self._repo.create_staff(login_name, email, full_name, role)

    async def stamp_consent(self, user_id: str, version: str) -> None:
        await self._repo.stamp_consent(user_id, version)

    async def set_status(self, user_id: str, status: UserStatus) -> None:
        await self._repo.set_status(user_id, status)

    async def decrypt_email(self, user: User) -> str | None:
        return await self._repo.decrypt_email(user)

    async def decrypt_login_name(self, user: User) -> str:
        return await self._repo.decrypt_login_name(user)

    async def decrypt_full_name(self, user: User) -> str | None:
        return await self._repo.decrypt_full_name(user)
