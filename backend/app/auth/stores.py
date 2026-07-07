from __future__ import annotations

import json
import secrets
import time
import uuid
from dataclasses import dataclass, field
from typing import Protocol

from app.models.user import User, UserRole, UserStatus


def new_token() -> str:
    return secrets.token_urlsafe(32)


@dataclass
class MagicLinkRecord:
    token: str
    user_id: str
    purpose: str


class SessionStore(Protocol):
    async def create(self, user_id: str) -> str: ...

    async def resolve(self, sid: str) -> str | None: ...

    async def revoke(self, sid: str) -> None: ...

    async def revoke_all_for_user(self, user_id: str) -> None: ...


class MagicLinkStore(Protocol):
    async def issue(self, user_id: str, purpose: str) -> str: ...

    async def consume(self, token: str) -> MagicLinkRecord | None: ...


class RateLimiter(Protocol):
    async def allow(
        self, action: str, subject: str, limit: int, window: int
    ) -> bool: ...


class UserStore(Protocol):
    async def get(self, user_id: str) -> User | None: ...

    async def get_by_login_hash(self, login_name: str) -> User | None: ...

    async def create_student(self, login_name: str, full_name: str | None) -> User: ...

    async def create_staff(
        self, login_name: str, email: str, full_name: str | None, role: UserRole
    ) -> User: ...

    async def stamp_consent(self, user_id: str, version: str) -> None: ...

    async def set_status(self, user_id: str, status: UserStatus) -> None: ...

    async def decrypt_email(self, user: User) -> str | None: ...


class InMemorySessionStore:
    def __init__(self, ttl_seconds: int = 1209600) -> None:
        self._ttl = ttl_seconds
        self._sessions: dict[str, tuple[str, float]] = {}
        self._by_user: dict[str, set[str]] = {}

    def _purge(self, sid: str) -> None:
        record = self._sessions.pop(sid, None)
        if record is None:
            return
        user_id, _ = record
        index = self._by_user.get(user_id)
        if index is not None:
            index.discard(sid)
            if not index:
                self._by_user.pop(user_id, None)

    async def create(self, user_id: str) -> str:
        sid = new_token()
        self._sessions[sid] = (user_id, time.time() + self._ttl)
        self._by_user.setdefault(user_id, set()).add(sid)
        return sid

    async def resolve(self, sid: str) -> str | None:
        record = self._sessions.get(sid)
        if record is None:
            return None
        user_id, expires_at = record
        if expires_at < time.time():
            self._purge(sid)
            return None
        return user_id

    async def revoke(self, sid: str) -> None:
        self._purge(sid)

    async def revoke_all_for_user(self, user_id: str) -> None:
        for sid in list(self._by_user.get(user_id, set())):
            self._purge(sid)


class InMemoryMagicLinkStore:
    def __init__(self, ttl_seconds: int = 900) -> None:
        self._ttl = ttl_seconds
        self._tokens: dict[str, tuple[str, str, float]] = {}

    async def issue(self, user_id: str, purpose: str) -> str:
        token = new_token()
        self._tokens[token] = (user_id, purpose, time.time() + self._ttl)
        return token

    async def consume(self, token: str) -> MagicLinkRecord | None:
        record = self._tokens.pop(token, None)
        if record is None:
            return None
        user_id, purpose, expires_at = record
        if expires_at < time.time():
            return None
        return MagicLinkRecord(token=token, user_id=user_id, purpose=purpose)


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, int] = {}

    async def allow(
        self, action: str, subject: str, limit: int, window: int
    ) -> bool:
        bucket = int(time.time()) // window
        key = f"{action}:{subject}:{bucket}"
        count = self._buckets.get(key, 0) + 1
        self._buckets[key] = count
        return count <= limit


@dataclass
class _MemUser:
    login_name: str
    email: str | None
    full_name: str | None
    role: UserRole
    status: UserStatus
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    consent_version: str | None = None
    consent_at: object | None = None


class InMemoryUserStore:
    def __init__(self) -> None:
        self._users: dict[str, _MemUser] = {}
        self._by_hash: dict[str, str] = {}

    def _hash(self, login_name: str) -> str:
        return login_name

    async def get(self, user_id: str) -> User | None:
        return self._users.get(str(user_id))  # type: ignore[return-value]

    async def get_by_login_hash(self, login_name: str) -> User | None:
        user_id = self._by_hash.get(self._hash(login_name))
        if user_id is None:
            return None
        return self._users.get(user_id)  # type: ignore[return-value]

    async def create_student(self, login_name: str, full_name: str | None) -> User:
        email = f"{login_name}@rsu.edu.lv"
        return await self._create(
            login_name, email, full_name, UserRole.student
        )

    async def create_staff(
        self, login_name: str, email: str, full_name: str | None, role: UserRole
    ) -> User:
        return await self._create(login_name, email, full_name, role)

    async def _create(
        self,
        login_name: str,
        email: str | None,
        full_name: str | None,
        role: UserRole,
    ) -> User:
        login_hash = self._hash(login_name)
        if login_hash in self._by_hash:
            raise ValueError("login_name already exists")
        user = _MemUser(
            login_name=login_name,
            email=email,
            full_name=full_name,
            role=role,
            status=UserStatus.invited,
        )
        self._users[str(user.id)] = user
        self._by_hash[login_hash] = str(user.id)
        return user  # type: ignore[return-value]

    async def stamp_consent(self, user_id: str, version: str) -> None:
        from datetime import datetime, timezone

        user = self._users.get(str(user_id))
        if user is None:
            return
        user.consent_version = version
        user.consent_at = datetime.now(timezone.utc)

    async def set_status(self, user_id: str, status: UserStatus) -> None:
        user = self._users.get(str(user_id))
        if user is None:
            return
        user.status = status

    async def decrypt_email(self, user: User) -> str | None:
        return user.email  # type: ignore[return-value]


class RedisSessionStore:
    def __init__(self, redis, ttl_seconds: int) -> None:
        self._redis = redis
        self._ttl = ttl_seconds

    def _index_key(self, user_id: str) -> str:
        return f"users:{user_id}:sessions"

    async def create(self, user_id: str) -> str:
        sid = new_token()
        payload = json.dumps({"user_id": str(user_id)})
        await self._redis.set(f"sess:{sid}", payload, ex=self._ttl)
        await self._redis.sadd(self._index_key(str(user_id)), sid)
        await self._redis.expire(self._index_key(str(user_id)), self._ttl)
        return sid

    async def resolve(self, sid: str) -> str | None:
        raw = await self._redis.get(f"sess:{sid}")
        if raw is None:
            return None
        return json.loads(raw)["user_id"]

    async def revoke(self, sid: str) -> None:
        raw = await self._redis.get(f"sess:{sid}")
        await self._redis.delete(f"sess:{sid}")
        if raw is not None:
            user_id = json.loads(raw)["user_id"]
            await self._redis.srem(self._index_key(str(user_id)), sid)

    async def revoke_all_for_user(self, user_id: str) -> None:
        index_key = self._index_key(str(user_id))
        sids = await self._redis.smembers(index_key)
        for sid in sids:
            await self._redis.delete(f"sess:{sid}")
        await self._redis.delete(index_key)


class RedisMagicLinkStore:
    def __init__(self, redis, ttl_seconds: int) -> None:
        self._redis = redis
        self._ttl = ttl_seconds

    async def issue(self, user_id: str, purpose: str) -> str:
        token = new_token()
        payload = json.dumps({"user_id": str(user_id), "purpose": purpose})
        await self._redis.set(f"ml:{token}", payload, ex=self._ttl)
        return token

    async def consume(self, token: str) -> MagicLinkRecord | None:
        raw = await self._redis.getdel(f"ml:{token}")
        if raw is None:
            return None
        data = json.loads(raw)
        return MagicLinkRecord(
            token=token, user_id=data["user_id"], purpose=data["purpose"]
        )


class RedisRateLimiter:
    def __init__(self, redis) -> None:
        self._redis = redis

    async def allow(
        self, action: str, subject: str, limit: int, window: int
    ) -> bool:
        bucket = int(time.time()) // window
        key = f"rl:{action}:{subject}:{bucket}"
        count = await self._redis.incr(key)
        if count == 1:
            await self._redis.expire(key, window)
        return count <= limit
