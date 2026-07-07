from __future__ import annotations

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKey
from app.models.case import Language


class AttemptStatus(enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"


class Attempt(UUIDPrimaryKey, Base):
    __tablename__ = "attempts"

    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    case_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("case_versions.id"),
        nullable=False,
        index=True,
    )
    language: Mapped[Language] = mapped_column(
        sa.Enum(Language, name="language"),
        nullable=False,
        default=Language.en,
    )
    assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("assignments.id"),
        nullable=True,
        index=True,
    )
    phase: Mapped[str] = mapped_column(sa.String(32), nullable=False, default="history")
    status: Mapped[AttemptStatus] = mapped_column(
        sa.Enum(AttemptStatus, name="attempt_status"),
        nullable=False,
        index=True,
        default=AttemptStatus.in_progress,
    )
    mode: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
