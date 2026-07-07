from __future__ import annotations

import re
from pathlib import Path

from strawberry.printer import print_schema

from app.api.graphql.schema import schema

SNAPSHOT = Path(__file__).parent / "schema.graphql"

CONTRACT_TYPES = {
    "CaseType",
    "FeedbackType",
    "FinalAnswerInput",
    "FinalAnswerType",
    "MessageType",
    "Mutation",
    "ScoresType",
    "SendBranch",
    "SendMessageResult",
    "SessionType",
}

CONTRACT_QUERY_FIELDS = [
    "ping: String!",
    "version: String!",
    "health: String!",
    "case(id: String!): CaseType",
    "session(id: String!): SessionType",
]


def _type_blocks(sdl: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in sdl.splitlines():
        header = re.match(r"^(type|input|enum|interface) (\w+)", line)
        if header and line.rstrip().endswith("{"):
            if current is not None:
                blocks[current] = "\n".join(buf)
            current = header.group(2)
            buf = [line]
        elif current is not None:
            buf.append(line)
            if line == "}":
                blocks[current] = "\n".join(buf)
                current = None
                buf = []
    return blocks


def test_schema_matches_frozen_snapshot():
    live = print_schema(schema) + "\n"
    frozen = SNAPSHOT.read_text()
    assert live == frozen, (
        "Live schema diverged from tests/schema.graphql. If intentional and "
        "additive, regenerate the snapshot; if it changes an existing "
        "operation, that is a contract break."
    )


def test_existing_contract_types_unchanged():
    blocks = _type_blocks(SNAPSHOT.read_text())
    for type_name in CONTRACT_TYPES:
        assert type_name in blocks, f"contract type {type_name} missing"

    mutation = blocks["Mutation"]
    expected_mutations = [
        "startCase(caseId: String!, mode: String!): SessionType!",
        "sendMessage(sessionId: String!, text: String!): SendMessageResult!",
        "requestExam(sessionId: String!): SessionType!",
        "sendTestOrder(sessionId: String!, text: String!): SessionType!",
        "setSummary(sessionId: String!, value: String!): SessionType!",
        "submitSummary(sessionId: String!): SessionType!",
        "setDifferentials(sessionId: String!, value: String!): SessionType!",
        "submitDifferentials(sessionId: String!): SessionType!",
        "setInterpretation(sessionId: String!, value: String!): SessionType!",
        "submitInterpretation(sessionId: String!): SessionType!",
        "setFinalAnswerField(sessionId: String!, fieldName: String!, value: String!): SessionType!",
        "requestHint(sessionId: String!): String!",
        "submitReflection(sessionId: String!, text: String!): SessionType!",
        "goToSummary(sessionId: String!, prompt: String!): SessionType!",
        "proposeDifferentials(sessionId: String!, prompt: String!): SessionType!",
        "interpretResults(sessionId: String!, prompt: String!): SessionType!",
        "submitFinal(sessionId: String!, prompt: String!): SessionType!",
        "orderInvestigations(sessionId: String!): SessionType!",
        "reflect(sessionId: String!): SessionType!",
    ]
    for line in expected_mutations:
        assert line in mutation, f"missing mutation: {line}"
    assert "submitFinalAnswer(" in mutation

    query = blocks["Query"]
    for line in CONTRACT_QUERY_FIELDS:
        assert line in query, f"missing query field: {line}"


def test_no_subscription_type():
    sdl = SNAPSHOT.read_text()
    assert "type Subscription" not in sdl
