from __future__ import annotations

import random

from app.services.projection import (
    EXAM_STUDENT_MSG,
    AttemptProjection,
    EventRecord,
    EventType,
    FinalAnswer,
    Message,
    fold,
)


def rec(seq: int, etype: EventType, **data) -> EventRecord:
    return EventRecord(type=etype.value, seq=seq, data=data)


def msg(message_id: str, mtype: str, text: str) -> Message:
    return Message(id=message_id, type=mtype, text=text)


def test_session_started_initializes_core_fields():
    proj = fold(
        [rec(1, EventType.SESSION_STARTED, id="a1", case_slug="xla", mode="exam")]
    )
    assert proj.id == "a1"
    assert proj.case_id == "xla"
    assert proj.mode == "exam"
    assert proj.phase == "history"
    assert proj.messages == []
    assert proj.ordered_tests == set()
    assert proj.hints_used == 0
    assert proj.exam_done is False
    assert proj.final_answer == FinalAnswer()
    assert proj.feedback is None


def test_system_and_student_messages_append_in_seq_order():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="practice"),
            rec(2, EventType.SYSTEM_MESSAGE_APPENDED, message_id="msg-1", text="opening"),
            rec(3, EventType.STUDENT_MESSAGE_SENT, message_id="msg-2", text="hi"),
        ]
    )
    assert proj.messages == [
        msg("msg-1", "system", "opening"),
        msg("msg-2", "student", "hi"),
    ]


def test_scid_nudge_appends_parent_then_tutor_and_ignores_rng():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="scid", mode="exam"),
            rec(
                2,
                EventType.SCID_NUDGE_FIRED,
                rng_draw=0.91,
                parent_message_id="msg-9",
                parent_text="worry",
                tutor_message_id="msg-10",
                tutor_text="note",
            ),
        ]
    )
    assert proj.messages == [
        msg("msg-9", "parent", "worry"),
        msg("msg-10", "tutor", "note"),
    ]


def test_phase_changed_sets_phase():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="exam"),
            rec(2, EventType.PHASE_CHANGED, from_phase="history", to_phase="tests"),
            rec(3, EventType.PHASE_CHANGED, from_phase="tests", to_phase="feedback"),
        ]
    )
    assert proj.phase == "feedback"


def test_test_ordered_accumulates_into_set():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="exam"),
            rec(2, EventType.TEST_ORDERED, key="CBC"),
            rec(3, EventType.TEST_ORDERED, key="immunoglobulins"),
            rec(4, EventType.TEST_ORDERED, key="CBC"),
        ]
    )
    assert proj.ordered_tests == {"CBC", "immunoglobulins"}


def test_lab_result_and_genetic_nudge_channels():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="practice"),
            rec(
                2,
                EventType.LAB_RESULT_SHOWN,
                message_id="msg-1",
                text="CBC result",
                key="CBC",
                is_genetic=False,
            ),
            rec(
                3,
                EventType.GENETIC_NUDGE_SHOWN,
                message_id="msg-2",
                text="genetic nudge",
            ),
        ]
    )
    assert proj.messages == [
        msg("msg-1", "lab", "CBC result"),
        msg("msg-2", "lab_tutor", "genetic nudge"),
    ]


def test_test_unavailable_and_order_batch_use_channel_field():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="exam"),
            rec(
                2,
                EventType.TEST_UNAVAILABLE_NOTED,
                message_id="msg-1",
                text="not available",
                key="MRI",
                channel="system",
            ),
            rec(
                3,
                EventType.TEST_UNAVAILABLE_NOTED,
                message_id="msg-2",
                text="not available lab",
                key="PET",
                channel="lab_note",
            ),
            rec(
                4,
                EventType.ORDER_BATCH_NOTED,
                message_id="msg-3",
                text="ordered",
                any_new=True,
                channel="system",
            ),
            rec(
                5,
                EventType.ORDER_BATCH_NOTED,
                message_id="msg-4",
                text="already",
                any_new=False,
                channel="lab_note",
            ),
        ]
    )
    assert proj.messages == [
        msg("msg-1", "system", "not available"),
        msg("msg-2", "lab_note", "not available lab"),
        msg("msg-3", "system", "ordered"),
        msg("msg-4", "lab_note", "already"),
    ]


def test_test_order_unrecognized_is_lab_note():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="exam"),
            rec(
                2,
                EventType.TEST_ORDER_UNRECOGNIZED,
                message_id="msg-1",
                text="warning",
            ),
        ]
    )
    assert proj.messages == [msg("msg-1", "lab_note", "warning")]


def test_parent_reply_requested_does_not_mutate_projection():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="exam"),
            rec(
                2,
                EventType.PARENT_REPLY_REQUESTED,
                system="be a parent",
                history=[{"role": "user", "content": "hi"}],
                max_tokens=300,
            ),
        ]
    )
    assert proj.messages == []
    assert proj.pending_parent is None


def test_parent_reply_appended_and_exam_nudge():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="practice"),
            rec(2, EventType.PARENT_REPLY_APPENDED, message_id="msg-1", text="reply"),
            rec(3, EventType.EXAM_NUDGE_SHOWN, message_id="msg-2", text="nudge"),
        ]
    )
    assert proj.messages == [
        msg("msg-1", "parent", "reply"),
        msg("msg-2", "tutor", "nudge"),
    ]


def test_exam_performed_folds_two_messages_and_sets_done():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="practice"),
            rec(
                2,
                EventType.EXAM_PERFORMED,
                student_message_id="msg-1",
                exam_message_id="msg-2",
                exam_text="findings",
            ),
            rec(
                3,
                EventType.EXAM_PATHOGNOMONIC_NOTED,
                message_id="msg-3",
                text="pathognomonic",
            ),
        ]
    )
    assert proj.messages == [
        msg("msg-1", "student", EXAM_STUDENT_MSG),
        msg("msg-2", "system", "findings"),
        msg("msg-3", "tutor", "pathognomonic"),
    ]
    assert proj.exam_done is True


def test_summary_set_and_evaluated():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="exam"),
            rec(2, EventType.SUMMARY_SET, value="my summary"),
            rec(
                3,
                EventType.SUMMARY_EVALUATED,
                tutor_message_id="msg-1",
                tutor_text="reasoning note",
                feedback="reasoning note",
            ),
        ]
    )
    assert proj.summary == "my summary"
    assert proj.messages == [msg("msg-1", "tutor", "reasoning note")]


def test_differentials_set_and_evaluated():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="exam"),
            rec(2, EventType.DIFFERENTIALS_SET, value="ddx"),
            rec(
                3,
                EventType.DIFFERENTIALS_EVALUATED,
                message_id="msg-1",
                text="ddx note",
                source="wrong_path",
                wrong_key="sepsis",
            ),
        ]
    )
    assert proj.differentials == "ddx"
    assert proj.messages == [msg("msg-1", "lab_tutor", "ddx note")]


def test_interp_text_set_and_evaluated_success():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="exam"),
            rec(2, EventType.INTERP_TEXT_SET, value="interp"),
            rec(
                3,
                EventType.INTERPRETATION_EVALUATED,
                interp_note_message_id="msg-1",
                interp_note_text="my interpretation",
                result_message_id="msg-2",
                result="good reasoning",
                error=False,
            ),
        ]
    )
    assert proj.interp_text == "interp"
    assert proj.interp_result == "good reasoning"
    assert proj.messages == [
        msg("msg-1", "lab_note", "my interpretation"),
        msg("msg-2", "lab_tutor", "good reasoning"),
    ]


def test_interpretation_evaluated_error_path():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="exam"),
            rec(
                2,
                EventType.INTERPRETATION_EVALUATED,
                interp_note_message_id="msg-1",
                interp_note_text="my interpretation",
                result_message_id="msg-2",
                result="connection error",
                error=True,
            ),
        ]
    )
    assert proj.interp_result == "connection error"
    assert proj.messages == [
        msg("msg-1", "lab_note", "my interpretation"),
        msg("msg-2", "lab_note", "connection error"),
    ]


def test_interpretation_reset_clears_interp_fields_only():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="exam"),
            rec(2, EventType.INTERP_TEXT_SET, value="interp"),
            rec(
                3,
                EventType.INTERPRETATION_EVALUATED,
                interp_note_message_id="msg-1",
                interp_note_text="my interpretation",
                result_message_id="msg-2",
                result="good reasoning",
                error=False,
            ),
            rec(4, EventType.TEST_ORDERED, key="CBC"),
            rec(5, EventType.INTERPRETATION_RESET),
        ]
    )
    assert proj.interp_text == ""
    assert proj.interp_result == ""
    assert proj.ordered_tests == {"CBC"}
    assert proj.messages == [
        msg("msg-1", "lab_note", "my interpretation"),
        msg("msg-2", "lab_tutor", "good reasoning"),
    ]


def test_final_answer_field_set_and_submitted():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="exam"),
            rec(2, EventType.FINAL_ANSWER_FIELD_SET, field_name="diagnosis", value="XLA"),
            rec(
                3,
                EventType.FINAL_ANSWER_FIELD_SET,
                field_name="management",
                value="IVIG",
            ),
            rec(
                4,
                EventType.FINAL_ANSWER_SUBMITTED,
                message_id="msg-1",
                ans_text="final answer",
            ),
        ]
    )
    assert proj.final_answer.diagnosis == "XLA"
    assert proj.final_answer.management == "IVIG"
    assert proj.messages == [msg("msg-1", "student", "final answer")]


def test_feedback_generated_sets_feedback_dict():
    feedback = {"scores": {"overall": 8}, "strengths": ["x"]}
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="exam"),
            rec(2, EventType.FEEDBACK_GENERATED, feedback=feedback),
        ]
    )
    assert proj.feedback == feedback


def test_hint_requested_increments_unconditionally():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="exam"),
            rec(2, EventType.HINT_REQUESTED, hint_text="hint one"),
            rec(3, EventType.HINT_REQUESTED, hint_text="HINT_FALLBACK"),
            rec(4, EventType.HINT_REQUESTED, hint_text="hint three"),
        ]
    )
    assert proj.hints_used == 3
    assert proj.messages == []


def test_reflection_answered_advanced_and_summarized():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="reflection"),
            rec(2, EventType.REFLECTION_ANSWERED, step=0, q="Q1", a="A1"),
            rec(3, EventType.REFLECTION_STEP_ADVANCED, to_step=1),
            rec(4, EventType.REFLECTION_ANSWERED, step=1, q="Q2", a="A2"),
            rec(5, EventType.REFLECTION_SUMMARIZED, message_id="msg-1", text="summary"),
        ]
    )
    assert proj.reflection_step == 1
    assert proj.reflection_answers == [
        {"q": "Q1", "a": "A1"},
        {"q": "Q2", "a": "A2"},
    ]
    assert proj.messages == [msg("msg-1", "tutor", "summary")]


def test_mode_changed_updates_mode():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="practice"),
            rec(2, EventType.MODE_CHANGED, from_mode="practice", to_mode="reflection"),
        ]
    )
    assert proj.mode == "reflection"


def test_tutor_prompt_appended_respects_channel():
    proj = fold(
        [
            rec(1, EventType.SESSION_STARTED, id="a", case_slug="xla", mode="exam"),
            rec(
                2,
                EventType.TUTOR_PROMPT_APPENDED,
                message_id="msg-1",
                text="tutor prompt",
                channel="tutor",
            ),
            rec(
                3,
                EventType.TUTOR_PROMPT_APPENDED,
                message_id="msg-2",
                text="lab tutor prompt",
                channel="lab_tutor",
            ),
        ]
    )
    assert proj.messages == [
        msg("msg-1", "tutor", "tutor prompt"),
        msg("msg-2", "lab_tutor", "lab tutor prompt"),
    ]


def _all_event_types_sequence() -> list[EventRecord]:
    return [
        rec(1, EventType.SESSION_STARTED, id="att", case_slug="scid", mode="practice"),
        rec(2, EventType.SYSTEM_MESSAGE_APPENDED, message_id="m1", text="opening"),
        rec(3, EventType.STUDENT_MESSAGE_SENT, message_id="m2", text="question"),
        rec(
            4,
            EventType.PARENT_REPLY_REQUESTED,
            system="parent",
            history=[{"role": "user", "content": "question"}],
            max_tokens=300,
        ),
        rec(5, EventType.PARENT_REPLY_APPENDED, message_id="m3", text="parent reply"),
        rec(
            6,
            EventType.SCID_NUDGE_FIRED,
            rng_draw=0.77,
            parent_message_id="m4",
            parent_text="worry",
            tutor_message_id="m5",
            tutor_text="scid note",
        ),
        rec(7, EventType.EXAM_NUDGE_SHOWN, message_id="m6", text="exam nudge"),
        rec(
            8,
            EventType.EXAM_PERFORMED,
            student_message_id="m7",
            exam_message_id="m8",
            exam_text="exam findings",
        ),
        rec(9, EventType.EXAM_PATHOGNOMONIC_NOTED, message_id="m9", text="pathognomonic"),
        rec(10, EventType.HINT_REQUESTED, hint_text="hint a"),
        rec(11, EventType.HINT_REQUESTED, hint_text="hint b"),
        rec(12, EventType.SUMMARY_SET, value="summary text"),
        rec(13, EventType.STUDENT_MESSAGE_SENT, message_id="m10", text="summary msg"),
        rec(
            14,
            EventType.SUMMARY_EVALUATED,
            tutor_message_id="m11",
            tutor_text="summary note",
            feedback="summary note",
        ),
        rec(15, EventType.PHASE_CHANGED, from_phase="history", to_phase="examination"),
        rec(16, EventType.DIFFERENTIALS_SET, value="ddx text"),
        rec(
            17,
            EventType.DIFFERENTIALS_EVALUATED,
            message_id="m12",
            text="ddx note",
            source="llm",
        ),
        rec(18, EventType.PHASE_CHANGED, from_phase="examination", to_phase="tests"),
        rec(19, EventType.TEST_ORDERED, key="CBC"),
        rec(
            20,
            EventType.LAB_RESULT_SHOWN,
            message_id="m13",
            text="CBC result",
            key="CBC",
            is_genetic=False,
        ),
        rec(21, EventType.TEST_ORDERED, key="gene panel"),
        rec(
            22,
            EventType.LAB_RESULT_SHOWN,
            message_id="m14",
            text="gene panel result",
            key="gene panel",
            is_genetic=True,
        ),
        rec(23, EventType.GENETIC_NUDGE_SHOWN, message_id="m15", text="genetic nudge"),
        rec(
            24,
            EventType.TEST_UNAVAILABLE_NOTED,
            message_id="m16",
            text="unavailable",
            key="MRI",
            channel="lab_note",
        ),
        rec(
            25,
            EventType.ORDER_BATCH_NOTED,
            message_id="m17",
            text="ordered batch",
            any_new=True,
            channel="lab_note",
        ),
        rec(
            26,
            EventType.TEST_ORDER_UNRECOGNIZED,
            message_id="m18",
            text="unrecognized",
        ),
        rec(27, EventType.INTERP_TEXT_SET, value="interp text"),
        rec(
            28,
            EventType.INTERPRETATION_EVALUATED,
            interp_note_message_id="m19",
            interp_note_text="my interp",
            result_message_id="m20",
            result="interp result",
            error=False,
        ),
        rec(29, EventType.INTERPRETATION_RESET),
        rec(30, EventType.FINAL_ANSWER_FIELD_SET, field_name="diagnosis", value="SCID"),
        rec(
            31,
            EventType.FINAL_ANSWER_SUBMITTED,
            message_id="m21",
            ans_text="final answer",
        ),
        rec(32, EventType.FEEDBACK_GENERATED, feedback={"scores": {"overall": 9}}),
        rec(33, EventType.PHASE_CHANGED, from_phase="tests", to_phase="feedback"),
        rec(34, EventType.REFLECTION_ANSWERED, step=0, q="Q1", a="A1"),
        rec(35, EventType.REFLECTION_STEP_ADVANCED, to_step=1),
        rec(36, EventType.REFLECTION_SUMMARIZED, message_id="m22", text="reflection"),
        rec(37, EventType.MODE_CHANGED, from_mode="practice", to_mode="reflection"),
        rec(
            38,
            EventType.TUTOR_PROMPT_APPENDED,
            message_id="m23",
            text="tutor prompt",
            channel="tutor",
        ),
    ]


def test_full_catalog_sequence_reconstructs_every_field():
    proj = fold(_all_event_types_sequence())

    assert proj.id == "att"
    assert proj.case_id == "scid"
    assert proj.mode == "reflection"
    assert proj.phase == "feedback"
    assert proj.hints_used == 2
    assert proj.ordered_tests == {"CBC", "gene panel"}
    assert proj.exam_done is True
    assert proj.summary == "summary text"
    assert proj.differentials == "ddx text"
    assert proj.interp_text == ""
    assert proj.interp_result == ""
    assert proj.final_answer.diagnosis == "SCID"
    assert proj.feedback == {"scores": {"overall": 9}}
    assert proj.reflection_step == 1
    assert proj.reflection_answers == [{"q": "Q1", "a": "A1"}]

    assert proj.messages == [
        msg("m1", "system", "opening"),
        msg("m2", "student", "question"),
        msg("m3", "parent", "parent reply"),
        msg("m4", "parent", "worry"),
        msg("m5", "tutor", "scid note"),
        msg("m6", "tutor", "exam nudge"),
        msg("m7", "student", EXAM_STUDENT_MSG),
        msg("m8", "system", "exam findings"),
        msg("m9", "tutor", "pathognomonic"),
        msg("m10", "student", "summary msg"),
        msg("m11", "tutor", "summary note"),
        msg("m12", "lab_tutor", "ddx note"),
        msg("m13", "lab", "CBC result"),
        msg("m14", "lab", "gene panel result"),
        msg("m15", "lab_tutor", "genetic nudge"),
        msg("m16", "lab_note", "unavailable"),
        msg("m17", "lab_note", "ordered batch"),
        msg("m18", "lab_note", "unrecognized"),
        msg("m19", "lab_note", "my interp"),
        msg("m20", "lab_tutor", "interp result"),
        msg("m21", "student", "final answer"),
        msg("m22", "tutor", "reflection"),
        msg("m23", "tutor", "tutor prompt"),
    ]


def test_fold_covers_all_thirty_two_event_types():
    seen = {EventType(r.type) for r in _all_event_types_sequence()}
    assert seen == set(EventType)
    assert len(set(EventType)) == 32


def test_fold_is_order_stable_by_seq_not_list_order():
    ordered = _all_event_types_sequence()
    shuffled = list(ordered)
    random.Random(1234).shuffle(shuffled)

    proj_ordered = fold(ordered)
    proj_shuffled = fold(shuffled)

    assert proj_shuffled == proj_ordered
    assert proj_shuffled.messages == proj_ordered.messages


def test_fold_empty_events_returns_default_projection():
    assert fold([]) == AttemptProjection()
