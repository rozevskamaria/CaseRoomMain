from __future__ import annotations

import json

from app.services.research_data import (
    TIMELINE_ALLOW_LIST,
    _scrub_timeline,
)

FREE_TEXT_KEYS = (
    "text",
    "value",
    "ans_text",
    "q",
    "a",
    "feedback",
    "interp_note_text",
    "result",
    "parent_text",
    "tutor_text",
    "exam_text",
    "hint_text",
    "message_id",
    "history",
    "system",
)


def test_scrub_drops_unexpected_free_text_key():
    data = {
        "key": "CBC",
        "text": "Patient mentioned their name is Janis Berzins",
        "value": "free text answer",
        "surprise_pii": "555-1234 john@rsu.edu.lv",
    }
    out = _scrub_timeline("TestOrdered", data)
    assert out == {"key": "CBC"}
    assert "text" not in out
    assert "surprise_pii" not in out


def test_scrub_phase_changed_keeps_only_structured():
    data = {
        "from_phase": "history",
        "to_phase": "tests",
        "note": "secret",
    }
    out = _scrub_timeline("PhaseChanged", data)
    assert out == {"from_phase": "history", "to_phase": "tests"}


def test_scrub_lab_result_drops_text_keeps_key_flag():
    data = {
        "message_id": "abc",
        "text": "WBC 12 — student wrote: my email is x@rsu.edu.lv",
        "key": "CBC",
        "is_genetic": False,
    }
    out = _scrub_timeline("LabResultShown", data)
    assert out == {"key": "CBC", "is_genetic": False}


def test_allow_list_never_contains_free_text_keys():
    for event_type, allowed in TIMELINE_ALLOW_LIST.items():
        for key in allowed:
            assert key not in FREE_TEXT_KEYS, (
                f"{event_type} allow-list leaks free-text key {key}"
            )


def test_unknown_event_type_drops_everything():
    out = _scrub_timeline("MysteryEvent", {"text": "leak", "key": "x"})
    assert out == {}


def test_scrubbed_output_has_no_free_text_value():
    leaky_events = [
        (
            "DifferentialsEvaluated",
            {"source": "wrong_path", "wrong_key": "sepsis", "text": "leaky-secret"},
            ["leaky-secret"],
        ),
        (
            "ReflectionAnswered",
            {"q": "why?", "a": "because-of-pii", "text": "leaky-secret"},
            ["leaky-secret", "because-of-pii", "why?"],
        ),
        (
            "FinalAnswerSubmitted",
            {"ans_text": "my final diagnosis", "message_id": "z"},
            ["my final diagnosis", "z"],
        ),
        (
            "InterpretationEvaluated",
            {"error": True, "result": "free-result", "interp_note_text": "note-pii"},
            ["free-result", "note-pii"],
        ),
    ]
    for event_type, data, must_be_absent in leaky_events:
        out = _scrub_timeline(event_type, data)
        blob = json.dumps(out)
        for forbidden in must_be_absent:
            assert forbidden not in blob, f"{event_type} leaked {forbidden}"
