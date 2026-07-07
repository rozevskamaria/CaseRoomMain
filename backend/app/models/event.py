from __future__ import annotations

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKey


class EventType(enum.Enum):
    SessionStarted = "SessionStarted"
    SystemMessageAppended = "SystemMessageAppended"
    StudentMessageSent = "StudentMessageSent"
    ScidNudgeFired = "ScidNudgeFired"
    PhaseChanged = "PhaseChanged"
    TestOrdered = "TestOrdered"
    LabResultShown = "LabResultShown"
    GeneticNudgeShown = "GeneticNudgeShown"
    TestUnavailableNoted = "TestUnavailableNoted"
    OrderBatchNoted = "OrderBatchNoted"
    TestOrderUnrecognized = "TestOrderUnrecognized"
    ParentReplyRequested = "ParentReplyRequested"
    ParentReplyAppended = "ParentReplyAppended"
    ExamNudgeShown = "ExamNudgeShown"
    ExamPerformed = "ExamPerformed"
    ExamPathognomonicNoted = "ExamPathognomonicNoted"
    SummarySet = "SummarySet"
    SummaryEvaluated = "SummaryEvaluated"
    DifferentialsSet = "DifferentialsSet"
    DifferentialsEvaluated = "DifferentialsEvaluated"
    InterpTextSet = "InterpTextSet"
    InterpretationEvaluated = "InterpretationEvaluated"
    InterpretationReset = "InterpretationReset"
    FinalAnswerFieldSet = "FinalAnswerFieldSet"
    FinalAnswerSubmitted = "FinalAnswerSubmitted"
    FeedbackGenerated = "FeedbackGenerated"
    HintRequested = "HintRequested"
    ReflectionAnswered = "ReflectionAnswered"
    ReflectionStepAdvanced = "ReflectionStepAdvanced"
    ReflectionSummarized = "ReflectionSummarized"
    ModeChanged = "ModeChanged"
    TutorPromptAppended = "TutorPromptAppended"


class Event(UUIDPrimaryKey, Base):
    __tablename__ = "events"
    __table_args__ = (
        sa.UniqueConstraint("attempt_id", "seq"),
        sa.Index("ix_events_attempt_id_seq", "attempt_id", "seq"),
    )

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("attempts.id"),
        nullable=False,
        index=True,
    )
    seq: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    type: Mapped[EventType] = mapped_column(
        sa.Enum(EventType, name="event_type"), nullable=False
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=func.now(), nullable=False
    )
