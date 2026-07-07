from __future__ import annotations

import importlib.util
import pathlib

MIGRATION = (
    pathlib.Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "0003_research_event_indexes.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("mig_0003", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_0003_loads_and_chains():
    module = _load()
    assert module.revision == "0003_research_event_indexes"
    assert module.down_revision == "0002_cohorts_assignments"
    assert callable(module.upgrade)
    assert callable(module.downgrade)
