import json
from pathlib import Path

import pytest

from app.content.cases.xla import XLA
from app.schemas.case import Case
from app.services.prompts import (
    REFLECTION_QS,
    build_hint_context,
    build_reflection_summary_prompt,
    make_differential_eval_prompt,
    make_feedback_prompt,
    make_interpretation_eval_prompt,
    make_summary_eval_prompt,
    make_tutor_prompt,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "parity"

CASES = {"xla": XLA}

EVAL_PROMPT_BUILDERS = {
    "summary": make_summary_eval_prompt,
    "differential": make_differential_eval_prompt,
    "interpretation": make_interpretation_eval_prompt,
}


def load_fixture(name):
    with open(FIXTURE_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def cases(name):
    return [(entry["input"], entry["output"]) for entry in load_fixture(name)]


def case_from_hint_input(inp):
    return Case(
        id="xla",
        title=inp["title"],
        topic="",
        patient="",
        difficulty="",
        opening_clinical="",
        opening="",
        target_diagnosis=inp["targetDiagnosis"],
        target_iuis="",
        red_flags=[],
        parent_prompt="",
        lab_data={k: "" for k in inp["labDataKeys"]},
        exam_findings="",
        model_diagnosis="",
        model_management="",
        model_genetic_counselling="",
        key_clues=inp["keyClues"],
        wrong_paths={},
    )


def msgs_from_hint_input(inp):
    msgs = [{"type": "parent"} for _ in range(inp["parentExchanges"])]
    student_questions = inp["studentQuestions"]
    if student_questions:
        for text in student_questions.split(" | "):
            msgs.append({"type": "student", "text": text})
    return msgs


@pytest.mark.parametrize("inp,expected", cases("makeTutorPrompt"))
def test_make_tutor_prompt(inp, expected):
    assert make_tutor_prompt(CASES[inp["case"]], inp["phase"], inp["mode"]) == expected


@pytest.mark.parametrize("inp,expected", cases("makeFeedbackPrompt"))
def test_make_feedback_prompt(inp, expected):
    assert make_feedback_prompt(CASES[inp["case"]]) == expected


@pytest.mark.parametrize("inp,expected", cases("composedTutorEval"))
def test_composed_tutor_eval(inp, expected):
    builder = EVAL_PROMPT_BUILDERS[inp["phase"]]
    assert builder(CASES[inp["case"]], inp["mode"]) == expected


@pytest.mark.parametrize("inp,expected", cases("tutorEvalSuffix"))
def test_tutor_eval_suffix(inp, expected):
    builder = EVAL_PROMPT_BUILDERS[inp["phase"]]
    composed = builder(CASES["xla"], "practice")
    assert composed.endswith("\n\n" + expected)


@pytest.mark.parametrize("inp,expected", cases("buildHintContext"))
def test_build_hint_context(inp, expected):
    case = case_from_hint_input(inp)
    msgs = msgs_from_hint_input(inp)
    result = build_hint_context(
        case, inp["phase"], msgs, inp["orderedList"], inp["hintsUsed"]
    )
    assert result["notYetOrdered"] == expected["notYetOrdered"]
    assert result["importantMissing"] == expected["importantMissing"]
    assert result["context"] == expected["context"]


@pytest.mark.parametrize("inp,expected", cases("reflection"))
def test_reflection(inp, expected):
    if inp.get("kind") == "REFLECTION_QS":
        assert REFLECTION_QS == expected
    else:
        assert build_reflection_summary_prompt(CASES[inp["case"]]) == expected
