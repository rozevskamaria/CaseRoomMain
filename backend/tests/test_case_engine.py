import json
from pathlib import Path

import pytest

from app.content.cases.xla import XLA
from app.services.case_engine import (
    detect_tests_in_message,
    find_lab_result,
    flag_row,
    is_test_order,
    parse_lab_text,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "parity"


def load_fixture(name):
    with open(FIXTURE_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def cases(name):
    return [(entry["input"], entry["output"]) for entry in load_fixture(name)]


@pytest.mark.parametrize("text,expected", cases("parseLabText"))
def test_parse_lab_text(text, expected):
    assert parse_lab_text(text) == expected


@pytest.mark.parametrize("value,expected", cases("flagRow"))
def test_flag_row(value, expected):
    assert flag_row(value) == expected


@pytest.mark.parametrize("text,expected", cases("detectTestsInMessage"))
def test_detect_tests_in_message(text, expected):
    assert detect_tests_in_message(text) == expected


@pytest.mark.parametrize("text,expected", cases("isTestOrder"))
def test_is_test_order(text, expected):
    assert is_test_order(text) == expected


@pytest.mark.parametrize("fragment,expected", cases("findLabResult"))
def test_find_lab_result(fragment, expected):
    result = find_lab_result(XLA.lab_data, fragment)
    assert (list(result) if result is not None else None) == expected
