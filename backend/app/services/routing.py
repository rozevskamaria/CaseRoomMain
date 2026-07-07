from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.schemas.case import Case
from app.services.case_engine import (
    TEST_ALIASES,
    detect_tests_in_message,
    find_lab_result,
    is_test_order,
)
from app.services.projection import AttemptProjection
from app.services.prompts import language_directive

ORDER_TEST_TOOL = "order_test"
REQUEST_EXAM_TOOL = "request_exam"
ASK_PARENT_TOOL = "ask_parent"


@dataclass
class TestOrderAction:
    keys: list[str]


@dataclass
class ExamAction:
    pass


@dataclass
class ParentAction:
    pass


@dataclass
class NoopAction:
    pass


RoutedAction = TestOrderAction | ExamAction | ParentAction | NoopAction


def case_test_keys(case: Case) -> list[str]:
    keys = []
    for entry in TEST_ALIASES:
        key = entry["key"]
        if find_lab_result(case.lab_data, key) is not None:
            keys.append(key)
    return list(dict.fromkeys(keys))


def build_case_tools(case: Case) -> list[dict[str, Any]]:
    test_keys = case_test_keys(case)
    return [
        {
            "name": ORDER_TEST_TOOL,
            "description": (
                "Order one or more clinical investigations for this patient. "
                "Call this whenever the student requests, orders, or asks to run "
                "any lab, panel, imaging, biopsy, culture, or genetic test — in "
                "any language. Each test_name MUST be chosen from the provided "
                "enum of tests available in this case."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "test_names": {
                        "type": "array",
                        "items": {"type": "string", "enum": test_keys},
                        "description": "One or more test identifiers from this case.",
                    }
                },
                "required": ["test_names"],
                "additionalProperties": False,
            },
        },
        {
            "name": REQUEST_EXAM_TOOL,
            "description": (
                "Perform or request a physical examination of the patient. Call "
                "this when the student asks to examine, inspect, palpate, "
                "auscultate, or look at the patient, in any language."
            ),
            "input_schema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "name": ASK_PARENT_TOOL,
            "description": (
                "Continue the history-taking conversation with the parent. Call "
                "this for any question or statement directed at the parent about "
                "symptoms, history, family, or daily life — the default when the "
                "student is talking, not ordering a test or an examination."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"utterance": {"type": "string"}},
                "additionalProperties": False,
            },
        },
    ]


def build_router_system_prompt(case: Case, language: str) -> str:
    base = (
        "You route a medical student's message in a clinical case simulation to "
        "exactly one action. Decide whether the student is ordering an "
        "investigation (order_test), requesting a physical examination "
        "(request_exam), or talking to the parent (ask_parent). Always call "
        "exactly one tool."
    )
    directive = language_directive(language)
    if not directive:
        return base
    return f"{base}\n\n{directive}"


class Router(Protocol):
    async def route(
        self, proj: AttemptProjection, case: Case, text: str
    ) -> RoutedAction: ...


class HeuristicRouter:
    async def route(
        self, proj: AttemptProjection, case: Case, text: str
    ) -> RoutedAction:
        if is_test_order(text):
            return TestOrderAction(detect_tests_in_message(text))
        return ParentAction()


@dataclass
class ToolUseRouter:
    llm: Any
    max_tokens: int = 512

    async def route(
        self, proj: AttemptProjection, case: Case, text: str
    ) -> RoutedAction:
        tools = build_case_tools(case)
        allowed = set(case_test_keys(case))
        system = build_router_system_prompt(case, proj.language)
        try:
            result = await self.llm.generate_with_tools(
                system=system,
                messages=[{"role": "user", "content": text}],
                tools=tools,
                max_tokens=self.max_tokens,
            )
        except Exception:
            return ParentAction()
        if result.refused:
            return ParentAction()
        call = result.first_tool_call
        if call is None:
            return ParentAction()
        if call.name == ORDER_TEST_TOOL:
            raw = call.input.get("test_names") or []
            keys = [k for k in dict.fromkeys(raw) if k in allowed]
            if not keys:
                return ParentAction()
            return TestOrderAction(keys)
        if call.name == REQUEST_EXAM_TOOL:
            return ExamAction()
        return ParentAction()


def select_router(
    routing: str,
    language: str,
    heuristic: Router,
    tool_use: Router,
) -> Router:
    if routing == "tool_use" or language != "en":
        return tool_use
    return heuristic
