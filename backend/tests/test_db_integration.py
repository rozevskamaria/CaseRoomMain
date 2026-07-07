from __future__ import annotations

import uuid

import pytest

from app.models.case import (
    Case as CaseModel,
    CaseLocalizationEN,
    CaseVersion,
    CaseVersionStatus,
    Language,
)
from app.models.event import EventType as ModelEventType
from app.repositories.attempt_repo import AttemptRepository, NewEvent
from app.services.projection import EXAM_STUDENT_MSG, EventRecord
from app.services.projection import EventType as ProjEventType
from app.services.projection import Message, fold

pytestmark = pytest.mark.dbintegration


MINIMAL_CONTENT = {
    "title": "Test Case",
    "patient": "Test patient",
    "opening_clinical": "Opening clinical vignette.",
    "opening": "Opening line.",
    "red_flags": ["flag one"],
    "parent_prompt": "You are a worried parent.",
    "lab_data": {"CBC": "WBC 12.0\nHb 11.0"},
    "exam_findings": "Findings.",
    "model_diagnosis": "Test diagnosis",
    "model_management": "Test management",
    "model_genetic_counselling": "Test counselling",
    "key_clues": ["clue one"],
    "wrong_paths": {"sepsis": "Reconsider sepsis."},
}


async def _seed_minimal_case(session, slug: str) -> CaseVersion:
    case = CaseModel(slug=slug)
    session.add(case)
    await session.flush()

    version = CaseVersion(
        case_id=case.id,
        version_no=1,
        status=CaseVersionStatus.published,
        difficulty="medium",
        target_diagnosis="Test diagnosis",
        topic="Test topic",
        iuis="Test IUIS",
        created_by=None,
    )
    session.add(version)
    await session.flush()

    case.current_version_id = version.id
    localization = CaseLocalizationEN(
        case_version_id=version.id,
        language=Language.en,
        content=MINIMAL_CONTENT,
    )
    session.add(localization)
    await session.flush()
    return version


def _representative_events() -> list[NewEvent]:
    return [
        NewEvent(
            type=ModelEventType.SessionStarted,
            data={"id": "placeholder", "case_slug": "dbtest", "mode": "practice"},
        ),
        NewEvent(
            type=ModelEventType.SystemMessageAppended,
            data={"message_id": "msg-1", "text": "opening"},
        ),
        NewEvent(
            type=ModelEventType.StudentMessageSent,
            data={"message_id": "msg-2", "text": "history question"},
        ),
        NewEvent(
            type=ModelEventType.ParentReplyRequested,
            data={
                "system": "parent",
                "history": [{"role": "user", "content": "history question"}],
                "max_tokens": 300,
            },
        ),
        NewEvent(
            type=ModelEventType.ParentReplyAppended,
            data={"message_id": "msg-3", "text": "parent reply"},
        ),
        NewEvent(
            type=ModelEventType.ExamPerformed,
            data={
                "student_message_id": "msg-4",
                "exam_message_id": "msg-5",
                "exam_text": "exam findings",
            },
        ),
        NewEvent(type=ModelEventType.HintRequested, data={"hint_text": "a hint"}),
        NewEvent(type=ModelEventType.TestOrdered, data={"key": "CBC"}),
        NewEvent(
            type=ModelEventType.LabResultShown,
            data={
                "message_id": "msg-6",
                "text": "CBC result",
                "key": "CBC",
                "is_genetic": False,
            },
        ),
        NewEvent(
            type=ModelEventType.PhaseChanged,
            data={"from_phase": "history", "to_phase": "tests"},
        ),
        NewEvent(
            type=ModelEventType.InterpretationReset,
            data={},
        ),
    ]


async def test_attempt_repo_roundtrip_and_fold(db_session):
    version = await _seed_minimal_case(db_session, "dbtest")
    repo = AttemptRepository(db_session)

    attempt = await repo.create_attempt(
        case_version_id=version.id,
        mode="practice",
        language="en",
        student_id=None,
    )
    assert isinstance(attempt.id, uuid.UUID)

    new_events = _representative_events()
    new_events[0].data["id"] = str(attempt.id)

    persisted = await repo.append_events(attempt.id, new_events)
    assert [row.seq for row in persisted] == list(range(1, len(new_events) + 1))

    loaded = await repo.load_events(attempt.id)
    assert [row.seq for row in loaded] == list(range(1, len(new_events) + 1))
    assert all(loaded[i].seq < loaded[i + 1].seq for i in range(len(loaded) - 1))

    records = [
        EventRecord(type=row.type.value, seq=row.seq, data=row.data) for row in loaded
    ]
    proj = fold(records)

    assert proj.id == str(attempt.id)
    assert proj.case_id == "dbtest"
    assert proj.mode == "practice"
    assert proj.phase == "tests"
    assert proj.hints_used == 1
    assert proj.exam_done is True
    assert proj.ordered_tests == {"CBC"}
    assert proj.interp_text == ""
    assert proj.interp_result == ""
    assert proj.messages == [
        Message("msg-1", "system", "opening"),
        Message("msg-2", "student", "history question"),
        Message("msg-3", "parent", "parent reply"),
        Message("msg-4", "student", EXAM_STUDENT_MSG),
        Message("msg-5", "system", "exam findings"),
        Message("msg-6", "lab", "CBC result"),
    ]


async def test_append_events_serializes_seq_across_calls(db_session):
    version = await _seed_minimal_case(db_session, "dbtest_seq")
    repo = AttemptRepository(db_session)
    attempt = await repo.create_attempt(
        case_version_id=version.id,
        mode="exam",
        language="en",
        student_id=None,
    )

    first = await repo.append_events(
        attempt.id,
        [
            NewEvent(
                type=ModelEventType.SessionStarted,
                data={"id": str(attempt.id), "case_slug": "dbtest_seq", "mode": "exam"},
            ),
            NewEvent(
                type=ModelEventType.SystemMessageAppended,
                data={"message_id": "msg-1", "text": "opening"},
            ),
        ],
    )
    assert [row.seq for row in first] == [1, 2]

    second = await repo.append_events(
        attempt.id,
        [
            NewEvent(
                type=ModelEventType.StudentMessageSent,
                data={"message_id": "msg-2", "text": "next"},
            ),
        ],
    )
    assert [row.seq for row in second] == [3]

    third = await repo.append_events(
        attempt.id,
        [
            NewEvent(type=ModelEventType.HintRequested, data={"hint_text": "h"}),
            NewEvent(type=ModelEventType.TestOrdered, data={"key": "CBC"}),
        ],
    )
    assert [row.seq for row in third] == [4, 5]

    loaded = await repo.load_events(attempt.id)
    seqs = [row.seq for row in loaded]
    assert seqs == [1, 2, 3, 4, 5]
    assert seqs == sorted(seqs)
    assert len(seqs) == len(set(seqs))


async def test_create_attempt_persists_with_projection_cache_defaults(db_session):
    version = await _seed_minimal_case(db_session, "dbtest_cache")
    repo = AttemptRepository(db_session)
    attempt = await repo.create_attempt(
        case_version_id=version.id,
        mode="practice",
        language="en",
        student_id=None,
    )

    fetched = await repo.get_attempt(attempt.id)
    assert fetched is not None
    assert fetched.case_version_id == version.id
    assert fetched.phase == "history"
    assert fetched.mode == "practice"
    assert fetched.language == Language.en

    await repo.update_projection_cache(
        attempt.id,
        phase="tests",
        status="in_progress",
        mode="practice",
        completed_at=None,
    )
    refetched = await repo.get_attempt(attempt.id)
    assert refetched.phase == "tests"


async def test_load_events_empty_for_fresh_attempt(db_session):
    version = await _seed_minimal_case(db_session, "dbtest_empty")
    repo = AttemptRepository(db_session)
    attempt = await repo.create_attempt(
        case_version_id=version.id,
        mode="exam",
        language="en",
        student_id=None,
    )
    assert await repo.load_events(attempt.id) == []
    assert fold([]).messages == []


def test_event_type_catalog_matches_projection_enum():
    model_values = {e.value for e in ModelEventType}
    proj_values = {e.value for e in ProjEventType}
    assert model_values == proj_values
    assert len(model_values) == 32
