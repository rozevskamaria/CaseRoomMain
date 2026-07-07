from __future__ import annotations

import enum
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKey


class UserRole(enum.Enum):
    admin = "admin"
    staff = "staff"
    student = "student"


class UserStatus(enum.Enum):
    active = "active"
    invited = "invited"
    disabled = "disabled"


class User(UUIDPrimaryKey, Base):
    __tablename__ = "users"

    login_name: Mapped[bytes] = mapped_column(sa.LargeBinary, nullable=False)
    login_name_hash: Mapped[str] = mapped_column(
        sa.String(64), nullable=False, unique=True
    )
    email: Mapped[bytes | None] = mapped_column(sa.LargeBinary, nullable=True)
    full_name: Mapped[bytes | None] = mapped_column(sa.LargeBinary, nullable=True)
    role: Mapped[UserRole] = mapped_column(
        sa.Enum(UserRole, name="user_role"),
        nullable=False,
        index=True,
        default=UserRole.student,
    )
    status: Mapped[UserStatus] = mapped_column(
        sa.Enum(UserStatus, name="user_status"),
        nullable=False,
        index=True,
        default=UserStatus.invited,
    )
    consent_version: Mapped[str | None] = mapped_column(sa.String(32), nullable=True)
    consent_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=func.now(), nullable=False
    )
