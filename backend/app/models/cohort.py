from __future__ import annotations

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKey


class CohortMembershipStatus(enum.Enum):
    active = "active"
    removed = "removed"


class CohortAuditAction(enum.Enum):
    enrolled = "enrolled"
    removed = "removed"
    reactivated = "reactivated"
    staff_assigned = "staff_assigned"
    staff_unassigned = "staff_unassigned"


class Cohort(UUIDPrimaryKey, Base):
    __tablename__ = "cohorts"

    slug: Mapped[str] = mapped_column(sa.String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    academic_year: Mapped[str | None] = mapped_column(
        sa.String(32), nullable=True, index=True
    )
    archived: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CohortMembership(UUIDPrimaryKey, Base):
    __tablename__ = "cohort_memberships"
    __table_args__ = (sa.UniqueConstraint("cohort_id", "student_id"),)

    cohort_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("cohorts.id"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[CohortMembershipStatus] = mapped_column(
        sa.Enum(CohortMembershipStatus, name="cohort_membership_status"),
        nullable=False,
        index=True,
        default=CohortMembershipStatus.active,
    )
    joined_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StaffCohort(UUIDPrimaryKey, Base):
    __tablename__ = "staff_cohorts"
    __table_args__ = (sa.UniqueConstraint("cohort_id", "staff_id"),)

    cohort_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("cohorts.id"), nullable=False, index=True
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CohortAuditLog(UUIDPrimaryKey, Base):
    __tablename__ = "cohort_audit_log"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True, index=True
    )
    cohort_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("cohorts.id"), nullable=False, index=True
    )
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True, index=True
    )
    action: Mapped[CohortAuditAction] = mapped_column(
        sa.Enum(CohortAuditAction, name="cohort_audit_action"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=func.now(), nullable=False
    )
