from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_cohorts_assignments"
down_revision = "0001_phase3_persistence"
branch_labels = None
depends_on = None


cohort_membership_status = postgresql.ENUM(
    "active", "removed", name="cohort_membership_status", create_type=False
)
cohort_audit_action = postgresql.ENUM(
    "enrolled",
    "removed",
    "reactivated",
    "staff_assigned",
    "staff_unassigned",
    name="cohort_audit_action",
    create_type=False,
)
language = postgresql.ENUM("en", "lv", name="language", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()

    cohort_membership_status.create(bind, checkfirst=True)
    cohort_audit_action.create(bind, checkfirst=True)

    op.create_table(
        "cohorts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("academic_year", sa.String(length=32), nullable=True),
        sa.Column(
            "archived",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_cohorts_created_by_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_cohorts"),
        sa.UniqueConstraint("slug", name="uq_cohorts_slug"),
    )
    op.create_index(
        "ix_cohorts_academic_year", "cohorts", ["academic_year"], unique=False
    )
    op.create_index(
        "ix_cohorts_created_by", "cohorts", ["created_by"], unique=False
    )

    op.create_table(
        "cohort_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", cohort_membership_status, nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["cohort_id"],
            ["cohorts.id"],
            name="fk_cohort_memberships_cohort_id_cohorts",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["users.id"],
            name="fk_cohort_memberships_student_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_cohort_memberships"),
        sa.UniqueConstraint(
            "cohort_id", "student_id", name="uq_cohort_memberships_cohort_id"
        ),
    )
    op.create_index(
        "ix_cohort_memberships_cohort_id",
        "cohort_memberships",
        ["cohort_id"],
        unique=False,
    )
    op.create_index(
        "ix_cohort_memberships_student_id",
        "cohort_memberships",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "ix_cohort_memberships_status",
        "cohort_memberships",
        ["status"],
        unique=False,
    )

    op.create_table(
        "staff_cohorts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("staff_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["cohort_id"],
            ["cohorts.id"],
            name="fk_staff_cohorts_cohort_id_cohorts",
        ),
        sa.ForeignKeyConstraint(
            ["staff_id"],
            ["users.id"],
            name="fk_staff_cohorts_staff_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_staff_cohorts"),
        sa.UniqueConstraint(
            "cohort_id", "staff_id", name="uq_staff_cohorts_cohort_id"
        ),
    )
    op.create_index(
        "ix_staff_cohorts_cohort_id", "staff_cohorts", ["cohort_id"], unique=False
    )
    op.create_index(
        "ix_staff_cohorts_staff_id", "staff_cohorts", ["staff_id"], unique=False
    )

    op.create_table(
        "cohort_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", cohort_audit_action, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name="fk_cohort_audit_log_actor_id_users",
        ),
        sa.ForeignKeyConstraint(
            ["cohort_id"],
            ["cohorts.id"],
            name="fk_cohort_audit_log_cohort_id_cohorts",
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["users.id"],
            name="fk_cohort_audit_log_subject_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_cohort_audit_log"),
    )
    op.create_index(
        "ix_cohort_audit_log_actor_id",
        "cohort_audit_log",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        "ix_cohort_audit_log_cohort_id",
        "cohort_audit_log",
        ["cohort_id"],
        unique=False,
    )
    op.create_index(
        "ix_cohort_audit_log_subject_id",
        "cohort_audit_log",
        ["subject_id"],
        unique=False,
    )
    op.create_index(
        "ix_cohort_audit_log_action",
        "cohort_audit_log",
        ["action"],
        unique=False,
    )

    op.create_table(
        "assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "case_version_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("title", sa.String(length=256), nullable=True),
        sa.Column("language", language, nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("opens_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["cohort_id"],
            ["cohorts.id"],
            name="fk_assignments_cohort_id_cohorts",
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name="fk_assignments_case_id_cases",
        ),
        sa.ForeignKeyConstraint(
            ["case_version_id"],
            ["case_versions.id"],
            name="fk_assignments_case_version_id_case_versions",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_assignments_created_by_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_assignments"),
    )
    op.create_index(
        "ix_assignments_cohort_id", "assignments", ["cohort_id"], unique=False
    )
    op.create_index(
        "ix_assignments_case_id", "assignments", ["case_id"], unique=False
    )
    op.create_index(
        "ix_assignments_case_version_id",
        "assignments",
        ["case_version_id"],
        unique=False,
    )
    op.create_index(
        "ix_assignments_created_by", "assignments", ["created_by"], unique=False
    )

    op.create_index(
        "ix_attempts_assignment_id", "attempts", ["assignment_id"], unique=False
    )
    op.create_foreign_key(
        "fk_attempts_assignment_id_assignments",
        "attempts",
        "assignments",
        ["assignment_id"],
        ["id"],
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_constraint(
        "fk_attempts_assignment_id_assignments", "attempts", type_="foreignkey"
    )
    op.drop_index("ix_attempts_assignment_id", table_name="attempts")

    op.drop_index("ix_assignments_created_by", table_name="assignments")
    op.drop_index("ix_assignments_case_version_id", table_name="assignments")
    op.drop_index("ix_assignments_case_id", table_name="assignments")
    op.drop_index("ix_assignments_cohort_id", table_name="assignments")
    op.drop_table("assignments")

    op.drop_index("ix_cohort_audit_log_action", table_name="cohort_audit_log")
    op.drop_index("ix_cohort_audit_log_subject_id", table_name="cohort_audit_log")
    op.drop_index("ix_cohort_audit_log_cohort_id", table_name="cohort_audit_log")
    op.drop_index("ix_cohort_audit_log_actor_id", table_name="cohort_audit_log")
    op.drop_table("cohort_audit_log")

    op.drop_index("ix_staff_cohorts_staff_id", table_name="staff_cohorts")
    op.drop_index("ix_staff_cohorts_cohort_id", table_name="staff_cohorts")
    op.drop_table("staff_cohorts")

    op.drop_index(
        "ix_cohort_memberships_status", table_name="cohort_memberships"
    )
    op.drop_index(
        "ix_cohort_memberships_student_id", table_name="cohort_memberships"
    )
    op.drop_index(
        "ix_cohort_memberships_cohort_id", table_name="cohort_memberships"
    )
    op.drop_table("cohort_memberships")

    op.drop_index("ix_cohorts_created_by", table_name="cohorts")
    op.drop_index("ix_cohorts_academic_year", table_name="cohorts")
    op.drop_table("cohorts")

    cohort_audit_action.drop(bind, checkfirst=True)
    cohort_membership_status.drop(bind, checkfirst=True)
