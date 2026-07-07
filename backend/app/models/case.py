from __future__ import annotations

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKey


class CaseVersionStatus(enum.Enum):
    draft = "draft"
    published = "published"


class Language(enum.Enum):
    en = "en"
    lv = "lv"


class CaseTestKind(enum.Enum):
    numeric_panel = "numeric_panel"
    imaging = "imaging"
    microbiology = "microbiology"
    genetic = "genetic"
    qualitative = "qualitative"


class Case(UUIDPrimaryKey, Base):
    __tablename__ = "cases"

    slug: Mapped[str] = mapped_column(sa.String(64), nullable=False, unique=True)
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("case_versions.id", use_alter=True),
        nullable=True,
    )


class CaseVersion(UUIDPrimaryKey, Base):
    __tablename__ = "case_versions"
    __table_args__ = (sa.UniqueConstraint("case_id", "version_no"),)

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("cases.id"),
        nullable=False,
        index=True,
    )
    version_no: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    status: Mapped[CaseVersionStatus] = mapped_column(
        sa.Enum(CaseVersionStatus, name="case_version_status"),
        nullable=False,
        index=True,
        default=CaseVersionStatus.draft,
    )
    difficulty: Mapped[str] = mapped_column(sa.String(32), nullable=False, index=True)
    target_diagnosis: Mapped[str] = mapped_column(
        sa.String(256), nullable=False, index=True
    )
    topic: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    iuis: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CaseLocalization(UUIDPrimaryKey, Base):
    __tablename__ = "case_localizations"
    __table_args__ = (sa.UniqueConstraint("case_version_id", "language"),)
    __mapper_args__ = {
        "polymorphic_on": "language",
        "polymorphic_abstract": True,
    }

    case_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("case_versions.id"),
        nullable=False,
        index=True,
    )
    language: Mapped[Language] = mapped_column(
        sa.Enum(Language, name="language"),
        nullable=False,
        index=True,
    )
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)


class CaseLocalizationEN(CaseLocalization):
    __mapper_args__ = {"polymorphic_identity": Language.en}


class CaseLocalizationLV(CaseLocalization):
    __mapper_args__ = {"polymorphic_identity": Language.lv}


class CaseTest(UUIDPrimaryKey, Base):
    __tablename__ = "case_tests"
    __table_args__ = (sa.UniqueConstraint("case_version_id", "key"),)
    __mapper_args__ = {
        "polymorphic_on": "kind",
        "polymorphic_abstract": True,
    }

    case_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("case_versions.id"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    kind: Mapped[CaseTestKind] = mapped_column(
        sa.Enum(CaseTestKind, name="test_kind"), nullable=False
    )
    ord: Mapped[int] = mapped_column(sa.Integer, nullable=False)


class NumericPanelTest(CaseTest):
    __tablename__ = "case_test_numeric_panels"
    __mapper_args__ = {"polymorphic_identity": CaseTestKind.numeric_panel}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("case_tests.id", ondelete="CASCADE"),
        primary_key=True,
    )


class ImagingTest(CaseTest):
    __tablename__ = "case_test_imaging"
    __mapper_args__ = {"polymorphic_identity": CaseTestKind.imaging}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("case_tests.id", ondelete="CASCADE"),
        primary_key=True,
    )
    modality: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    findings: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class MicrobiologyTest(CaseTest):
    __tablename__ = "case_test_microbiology"
    __mapper_args__ = {"polymorphic_identity": CaseTestKind.microbiology}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("case_tests.id", ondelete="CASCADE"),
        primary_key=True,
    )
    organism: Mapped[str | None] = mapped_column(sa.String(256), nullable=True)
    growth: Mapped[str | None] = mapped_column(sa.String(256), nullable=True)
    sensitivity: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class GeneticTest(CaseTest):
    __tablename__ = "case_test_genetic"
    __mapper_args__ = {"polymorphic_identity": CaseTestKind.genetic}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("case_tests.id", ondelete="CASCADE"),
        primary_key=True,
    )
    gene: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    variant: Mapped[str | None] = mapped_column(sa.String(256), nullable=True)
    classification: Mapped[str | None] = mapped_column(sa.String(128), nullable=True)
    interpretation: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class QualitativeTest(CaseTest):
    __tablename__ = "case_test_qualitative"
    __mapper_args__ = {"polymorphic_identity": CaseTestKind.qualitative}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("case_tests.id", ondelete="CASCADE"),
        primary_key=True,
    )
    result: Mapped[str | None] = mapped_column(sa.String(32), nullable=True)
    note: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class CaseTestAnalyte(UUIDPrimaryKey, Base):
    __tablename__ = "case_test_analytes"

    case_test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("case_tests.id"),
        nullable=False,
        index=True,
    )
    analyte: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    value: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    unit: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    ref_range: Mapped[str | None] = mapped_column(sa.String(128), nullable=True)
    flag: Mapped[str | None] = mapped_column(sa.String(16), nullable=True)
    ord: Mapped[int] = mapped_column(sa.Integer, nullable=False)


class CaseTestLocalization(UUIDPrimaryKey, Base):
    __tablename__ = "case_test_localizations"
    __table_args__ = (sa.UniqueConstraint("case_test_id", "language"),)

    case_test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("case_tests.id"),
        nullable=False,
        index=True,
    )
    language: Mapped[Language] = mapped_column(
        sa.Enum(Language, name="language"),
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    narrative: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
