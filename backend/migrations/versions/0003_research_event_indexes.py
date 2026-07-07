from __future__ import annotations

from alembic import op

revision = "0003_research_event_indexes"
down_revision = "0002_cohorts_assignments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_events_type", "events", ["type"], unique=False)
    op.execute(
        "CREATE INDEX ix_events_type_wrong_key ON events ((data->>'wrong_key')) "
        "WHERE type = 'DifferentialsEvaluated'"
    )
    op.execute(
        "CREATE INDEX ix_events_type_key ON events ((data->>'key')) "
        "WHERE type IN ('TestOrdered', 'LabResultShown', 'TestUnavailableNoted')"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_events_type_key")
    op.execute("DROP INDEX IF EXISTS ix_events_type_wrong_key")
    op.drop_index("ix_events_type", table_name="events")
