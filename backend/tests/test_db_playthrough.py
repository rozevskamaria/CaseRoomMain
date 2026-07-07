from __future__ import annotations

import itertools
import uuid

import pytest

from app.db.seed import seed
from app.repositories.attempt_repo import AttemptRepository
from app.repositories.case_repo import CaseRepository
from app.services.projection import EventRecord, fold
from app.services.session import SessionService
from app.services.stores import DbAttemptStore, DbCaseSource

pytestmark = pytest.mark.dbintegration


FEEDBACK_JSON = {
    "diagnosticAccuracy": "correct",
    "diagnosticComment": "XLA is the correct diagnosis.",
    "wellDone": ["Recognised the absent B cells", "Spotted the X-linked family history"],
    "missing": ["Could have screened for Giardia earlier"],
    "keyClues": ["Onset at 6 months", "Absent tonsils", "Absent CD19 B cells"],
    "reasoningPathway": "Recurrent encapsulated infections from 6m, absent B cells, BTK variant.",
    "managementPoints": ["Start IVIG", "Contraindicate live vaccines"],
    "geneticPoints": ["X-linked recessive", "Mother obligate carrier"],
    "revisionTopic": "Approach to recurrent bacterial infection in infancy.",
    "scores": {
        "historyTaking": "Good",
        "examination": "Good",
        "differential": "Excellent",
        "testSelection": "Good",
        "interpretation": "Excellent",
        "management": "Good",
    },
}


class FakeLLMClient:
    def __init__(self) -> None:
        self.parent_reply = "He started getting infections at about six months of age."

    async def generate(self, system, messages, max_tokens):
        return "Good reasoning — consider the B-cell compartment next."

    async def generate_structured(self, system, messages, schema, max_tokens):
        return dict(FEEDBACK_JSON)

    async def stream(self, system, messages, max_tokens):
        yield self.parent_reply


def _ids():
    counter = itertools.count(1)
    return lambda: f"id-{next(counter)}"


FINAL_ANSWER_FIELDS = {
    "diagnosis": "X-linked agammaglobulinaemia (XLA)",
    "findings": "Absent B cells, absent tonsils, infections from 6 months",
    "differentials": "CVID, THI",
    "tests": "Immunoglobulins, flow cytometry, BTK panel",
    "management": "IVIG, treat Giardia, no live vaccines",
    "genetics": "X-linked recessive, mother is carrier",
    "explanation": "His immune system cannot make antibodies.",
}


async def test_db_full_playthrough_and_replay_fidelity(db_session):
    await seed(db_session)
    await db_session.flush()

    llm = FakeLLMClient()
    case_repo = CaseRepository(db_session)
    attempt_repo = AttemptRepository(db_session)
    service = SessionService(
        llm,
        store=DbAttemptStore(attempt_repo, case_repo),
        cases=DbCaseSource(case_repo),
        rng=lambda: 0.0,
        id_factory=_ids(),
    )

    proj = await service.start_case("xla", "practice")
    attempt_id = proj.id
    assert proj.phase == "history"
    assert proj.messages[0].type == "system"
    assert proj.messages[0].text.startswith("📍 Immunology Department — Outpatient Clinic")

    history_questions = [
        "When did the infections start?",
        "What kind of infections has he had?",
        "Has he had all his vaccines?",
        "Are there any unexplained deaths in the family?",
        "How is his growth and weight?",
    ]
    for q in history_questions:
        result, _ = await service.send_message(attempt_id, q)
        assert result.branch == "parent"
        proj = await service.append_parent_reply(attempt_id, llm.parent_reply)

    parent_msgs = [m for m in proj.messages if m.type == "parent"]
    assert len(parent_msgs) == len(history_questions)
    assert parent_msgs[-1].text == llm.parent_reply

    proj = await service.send_test_order(attempt_id, "immunoglobulins")
    assert proj.phase == "tests"
    assert "immunoglobulin" in proj.ordered_tests
    lab_msgs = [m for m in proj.messages if m.type == "lab"]
    assert len(lab_msgs) == 1
    ig_lab = lab_msgs[0]
    assert ig_lab.text.startswith("__LAB__immunoglobulins")
    assert "IgG: <100" in ig_lab.text
    assert "IgA: <5" in ig_lab.text

    proj = await service.request_exam(attempt_id)
    assert proj.exam_done is True
    exam_msg = next(
        m for m in proj.messages if m.text.startswith("📋 Physical examination findings:")
    )
    assert "No visible tonsils" in exam_msg.text

    await service.go_to_summary(attempt_id, "Summarise the case.")
    await service.set_summary(attempt_id, "2yo boy, bacterial infections from 6 months, absent tonsils.")
    proj = await service.submit_summary(attempt_id)
    assert proj.summary.startswith("2yo boy")
    assert proj.phase == "examination"

    await service.go_to_differential(attempt_id, "Propose your differentials.")
    await service.set_differentials(attempt_id, "CVID is possible")
    proj = await service.submit_differentials(attempt_id)
    assert proj.differentials == "CVID is possible"
    assert proj.messages[-1].type == "lab_tutor"

    await service.go_to_differential(attempt_id, "Reconsider your differentials.")
    await service.set_differentials(attempt_id, "X-linked agammaglobulinaemia given absent B cells")
    proj = await service.submit_differentials(attempt_id)
    assert proj.differentials == "X-linked agammaglobulinaemia given absent B cells"
    assert proj.messages[-1].type == "lab_tutor"

    await service.go_to_interpretation(attempt_id, "Interpret the results.")
    await service.set_interp_text(attempt_id, "Absent B cells with absent immunoglobulins fit XLA.")
    proj = await service.submit_interpretation(attempt_id)
    assert proj.phase == "interpretation"
    assert proj.interp_result != ""
    assert proj.messages[-1].type == "lab_tutor"

    await service.go_to_final(attempt_id, "Submit your final diagnosis.")
    for field_name, value in FINAL_ANSWER_FIELDS.items():
        await service.set_final_answer_field(attempt_id, field_name, value)
    played = await service.submit_final_answer(attempt_id)

    assert played.phase == "feedback"
    assert played.feedback == FEEDBACK_JSON
    assert played.feedback["diagnosticAccuracy"] == "correct"
    assert played.feedback["scores"]["differential"] == "Excellent"
    assert played.final_answer.diagnosis == FINAL_ANSWER_FIELDS["diagnosis"]
    assert played.final_answer.explanation == FINAL_ANSWER_FIELDS["explanation"]

    fresh_repo = AttemptRepository(db_session)
    loaded = await fresh_repo.load_events(uuid.UUID(attempt_id))
    seqs = [row.seq for row in loaded]
    assert seqs == list(range(1, len(loaded) + 1))
    assert seqs[0] == 1
    assert all(seqs[i] + 1 == seqs[i + 1] for i in range(len(seqs) - 1))

    records = [
        EventRecord(type=row.type.value, seq=row.seq, data=row.data) for row in loaded
    ]
    reloaded = fold(records)

    assert reloaded is not played

    played_messages = [(m.id, m.type, m.text) for m in played.messages]
    reloaded_messages = [(m.id, m.type, m.text) for m in reloaded.messages]
    assert reloaded_messages == played_messages

    assert reloaded.ordered_tests == played.ordered_tests
    assert reloaded.phase == played.phase
    assert reloaded.exam_done == played.exam_done
    assert reloaded.summary == played.summary
    assert reloaded.differentials == played.differentials
    assert reloaded.interp_text == played.interp_text
    assert reloaded.interp_result == played.interp_result
    assert reloaded.final_answer == played.final_answer
    assert reloaded.feedback == played.feedback
    assert reloaded.hints_used == played.hints_used
