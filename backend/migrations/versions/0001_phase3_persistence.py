from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_phase3_persistence"
down_revision = None
branch_labels = None
depends_on = None


user_role = postgresql.ENUM(
    "admin", "staff", "student", name="user_role", create_type=False
)
user_status = postgresql.ENUM(
    "active", "invited", "disabled", name="user_status", create_type=False
)
case_version_status = postgresql.ENUM(
    "draft", "published", name="case_version_status", create_type=False
)
language = postgresql.ENUM("en", "lv", name="language", create_type=False)
test_kind = postgresql.ENUM(
    "numeric_panel",
    "imaging",
    "microbiology",
    "genetic",
    "qualitative",
    name="test_kind",
    create_type=False,
)
attempt_status = postgresql.ENUM(
    "in_progress",
    "completed",
    "abandoned",
    name="attempt_status",
    create_type=False,
)
event_type = postgresql.ENUM(
    "SessionStarted",
    "SystemMessageAppended",
    "StudentMessageSent",
    "ScidNudgeFired",
    "PhaseChanged",
    "TestOrdered",
    "LabResultShown",
    "GeneticNudgeShown",
    "TestUnavailableNoted",
    "OrderBatchNoted",
    "TestOrderUnrecognized",
    "ParentReplyRequested",
    "ParentReplyAppended",
    "ExamNudgeShown",
    "ExamPerformed",
    "ExamPathognomonicNoted",
    "SummarySet",
    "SummaryEvaluated",
    "DifferentialsSet",
    "DifferentialsEvaluated",
    "InterpTextSet",
    "InterpretationEvaluated",
    "InterpretationReset",
    "FinalAnswerFieldSet",
    "FinalAnswerSubmitted",
    "FeedbackGenerated",
    "HintRequested",
    "ReflectionAnswered",
    "ReflectionStepAdvanced",
    "ReflectionSummarized",
    "ModeChanged",
    "TutorPromptAppended",
    name="event_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    user_role.create(bind, checkfirst=True)
    user_status.create(bind, checkfirst=True)
    case_version_status.create(bind, checkfirst=True)
    language.create(bind, checkfirst=True)
    test_kind.create(bind, checkfirst=True)
    attempt_status.create(bind, checkfirst=True)
    event_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("login_name", sa.LargeBinary(), nullable=False),
        sa.Column("login_name_hash", sa.String(length=64), nullable=False),
        sa.Column("email", sa.LargeBinary(), nullable=True),
        sa.Column("full_name", sa.LargeBinary(), nullable=True),
        sa.Column("role", user_role, nullable=False),
        sa.Column("status", user_status, nullable=False),
        sa.Column("consent_version", sa.String(length=32), nullable=True),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("login_name_hash", name="uq_users_login_name_hash"),
    )
    op.create_index("ix_users_role", "users", ["role"], unique=False)
    op.create_index("ix_users_status", "users", ["status"], unique=False)

    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column(
            "current_version_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.PrimaryKeyConstraint("id", name="pk_cases"),
        sa.UniqueConstraint("slug", name="uq_cases_slug"),
    )

    op.create_table(
        "case_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("status", case_version_status, nullable=False),
        sa.Column("difficulty", sa.String(length=32), nullable=False),
        sa.Column("target_diagnosis", sa.String(length=256), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("iuis", sa.String(length=128), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name="fk_case_versions_case_id_cases",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_case_versions_created_by_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_case_versions"),
        sa.UniqueConstraint(
            "case_id", "version_no", name="uq_case_versions_case_id"
        ),
    )
    op.create_index(
        "ix_case_versions_case_id", "case_versions", ["case_id"], unique=False
    )
    op.create_index(
        "ix_case_versions_status", "case_versions", ["status"], unique=False
    )
    op.create_index(
        "ix_case_versions_difficulty",
        "case_versions",
        ["difficulty"],
        unique=False,
    )
    op.create_index(
        "ix_case_versions_target_diagnosis",
        "case_versions",
        ["target_diagnosis"],
        unique=False,
    )
    op.create_index(
        "ix_case_versions_topic", "case_versions", ["topic"], unique=False
    )
    op.create_index(
        "ix_case_versions_iuis", "case_versions", ["iuis"], unique=False
    )

    op.create_foreign_key(
        "fk_cases_current_version_id_case_versions",
        "cases",
        "case_versions",
        ["current_version_id"],
        ["id"],
        use_alter=True,
    )

    op.create_table(
        "case_localizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "case_version_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("language", language, nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_version_id"],
            ["case_versions.id"],
            name="fk_case_localizations_case_version_id_case_versions",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_case_localizations"),
        sa.UniqueConstraint(
            "case_version_id",
            "language",
            name="uq_case_localizations_case_version_id",
        ),
    )
    op.create_index(
        "ix_case_localizations_case_version_id",
        "case_localizations",
        ["case_version_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_localizations_language",
        "case_localizations",
        ["language"],
        unique=False,
    )

    op.create_table(
        "case_tests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "case_version_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("kind", test_kind, nullable=False),
        sa.Column("ord", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_version_id"],
            ["case_versions.id"],
            name="fk_case_tests_case_version_id_case_versions",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_case_tests"),
        sa.UniqueConstraint(
            "case_version_id", "key", name="uq_case_tests_case_version_id"
        ),
    )
    op.create_index(
        "ix_case_tests_case_version_id",
        "case_tests",
        ["case_version_id"],
        unique=False,
    )
    op.create_index("ix_case_tests_key", "case_tests", ["key"], unique=False)

    op.create_table(
        "case_test_numeric_panels",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["id"],
            ["case_tests.id"],
            name="fk_case_test_numeric_panels_id_case_tests",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_case_test_numeric_panels"),
    )

    op.create_table(
        "case_test_imaging",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("modality", sa.String(length=64), nullable=True),
        sa.Column("findings", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"],
            ["case_tests.id"],
            name="fk_case_test_imaging_id_case_tests",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_case_test_imaging"),
    )

    op.create_table(
        "case_test_microbiology",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organism", sa.String(length=256), nullable=True),
        sa.Column("growth", sa.String(length=256), nullable=True),
        sa.Column("sensitivity", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"],
            ["case_tests.id"],
            name="fk_case_test_microbiology_id_case_tests",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_case_test_microbiology"),
    )

    op.create_table(
        "case_test_genetic",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gene", sa.String(length=64), nullable=True),
        sa.Column("variant", sa.String(length=256), nullable=True),
        sa.Column("classification", sa.String(length=128), nullable=True),
        sa.Column("interpretation", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"],
            ["case_tests.id"],
            name="fk_case_test_genetic_id_case_tests",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_case_test_genetic"),
    )

    op.create_table(
        "case_test_qualitative",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("result", sa.String(length=32), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"],
            ["case_tests.id"],
            name="fk_case_test_qualitative_id_case_tests",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_case_test_qualitative"),
    )

    op.create_table(
        "case_test_analytes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_test_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analyte", sa.String(length=128), nullable=False),
        sa.Column("value", sa.String(length=256), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=True),
        sa.Column("ref_range", sa.String(length=128), nullable=True),
        sa.Column("flag", sa.String(length=16), nullable=True),
        sa.Column("ord", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_test_id"],
            ["case_tests.id"],
            name="fk_case_test_analytes_case_test_id_case_tests",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_case_test_analytes"),
    )
    op.create_index(
        "ix_case_test_analytes_case_test_id",
        "case_test_analytes",
        ["case_test_id"],
        unique=False,
    )

    op.create_table(
        "case_test_localizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_test_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", language, nullable=False),
        sa.Column("display_name", sa.String(length=256), nullable=False),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["case_test_id"],
            ["case_tests.id"],
            name="fk_case_test_localizations_case_test_id_case_tests",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_case_test_localizations"),
        sa.UniqueConstraint(
            "case_test_id",
            "language",
            name="uq_case_test_localizations_case_test_id",
        ),
    )
    op.create_index(
        "ix_case_test_localizations_case_test_id",
        "case_test_localizations",
        ["case_test_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_test_localizations_language",
        "case_test_localizations",
        ["language"],
        unique=False,
    )

    op.create_table(
        "attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "case_version_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("language", language, nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("phase", sa.String(length=32), nullable=False),
        sa.Column("status", attempt_status, nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["users.id"],
            name="fk_attempts_student_id_users",
        ),
        sa.ForeignKeyConstraint(
            ["case_version_id"],
            ["case_versions.id"],
            name="fk_attempts_case_version_id_case_versions",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_attempts"),
    )
    op.create_index(
        "ix_attempts_student_id", "attempts", ["student_id"], unique=False
    )
    op.create_index(
        "ix_attempts_case_version_id",
        "attempts",
        ["case_version_id"],
        unique=False,
    )
    op.create_index("ix_attempts_status", "attempts", ["status"], unique=False)

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("type", event_type, nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["attempts.id"],
            name="fk_events_attempt_id_attempts",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_events"),
        sa.UniqueConstraint("attempt_id", "seq", name="uq_events_attempt_id"),
    )
    op.create_index(
        "ix_events_attempt_id", "events", ["attempt_id"], unique=False
    )
    op.create_index(
        "ix_events_attempt_id_seq", "events", ["attempt_id", "seq"], unique=False
    )

    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["attempts.id"],
            name="fk_feedback_attempt_id_attempts",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_feedback"),
    )
    op.create_index(
        "ix_feedback_attempt_id", "feedback", ["attempt_id"], unique=False
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_feedback_attempt_id", table_name="feedback")
    op.drop_table("feedback")

    op.drop_index("ix_events_attempt_id_seq", table_name="events")
    op.drop_index("ix_events_attempt_id", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_attempts_status", table_name="attempts")
    op.drop_index("ix_attempts_case_version_id", table_name="attempts")
    op.drop_index("ix_attempts_student_id", table_name="attempts")
    op.drop_table("attempts")

    op.drop_index(
        "ix_case_test_localizations_language", table_name="case_test_localizations"
    )
    op.drop_index(
        "ix_case_test_localizations_case_test_id",
        table_name="case_test_localizations",
    )
    op.drop_table("case_test_localizations")

    op.drop_index(
        "ix_case_test_analytes_case_test_id", table_name="case_test_analytes"
    )
    op.drop_table("case_test_analytes")

    op.drop_table("case_test_qualitative")
    op.drop_table("case_test_genetic")
    op.drop_table("case_test_microbiology")
    op.drop_table("case_test_imaging")
    op.drop_table("case_test_numeric_panels")

    op.drop_index("ix_case_tests_key", table_name="case_tests")
    op.drop_index("ix_case_tests_case_version_id", table_name="case_tests")
    op.drop_table("case_tests")

    op.drop_index(
        "ix_case_localizations_language", table_name="case_localizations"
    )
    op.drop_index(
        "ix_case_localizations_case_version_id", table_name="case_localizations"
    )
    op.drop_table("case_localizations")

    op.drop_constraint(
        "fk_cases_current_version_id_case_versions", "cases", type_="foreignkey"
    )

    op.drop_index("ix_case_versions_iuis", table_name="case_versions")
    op.drop_index("ix_case_versions_topic", table_name="case_versions")
    op.drop_index(
        "ix_case_versions_target_diagnosis", table_name="case_versions"
    )
    op.drop_index("ix_case_versions_difficulty", table_name="case_versions")
    op.drop_index("ix_case_versions_status", table_name="case_versions")
    op.drop_index("ix_case_versions_case_id", table_name="case_versions")
    op.drop_table("case_versions")

    op.drop_table("cases")

    op.drop_index("ix_users_status", table_name="users")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_table("users")

    event_type.drop(bind, checkfirst=True)
    attempt_status.drop(bind, checkfirst=True)
    test_kind.drop(bind, checkfirst=True)
    language.drop(bind, checkfirst=True)
    case_version_status.drop(bind, checkfirst=True)
    user_status.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)

    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
