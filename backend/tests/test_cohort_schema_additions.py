from __future__ import annotations

from pathlib import Path

from strawberry.printer import print_schema

from app.api.graphql.schema import schema

SNAPSHOT = Path(__file__).parent / "schema.graphql"

NEW_TYPES = [
    "type CohortType {",
    "type CohortStudentType {",
    "type AssignmentType {",
    "type CohortMembershipResult {",
    "type AddStudentResult {",
    "type StudentLookupResult {",
    "type CohortAuditEntry {",
    "input CreateCohortInput {",
    "input CreateAssignmentInput {",
]

NEW_QUERY_FIELDS = [
    "myCohorts: [CohortType!]!",
    "cohort(id: String!): CohortType",
    "cohortRoster(cohortId: String!): [CohortStudentType!]!",
    "cohortStudent(cohortId: String!, studentId: String!): CohortStudentType",
    "studentAttempts(cohortId: String!, studentId: String!): [AttemptType!]!",
    "assignmentsForCohort(cohortId: String!): [AssignmentType!]!",
    "lookupStudent(cohortId: String!, loginName: String!): StudentLookupResult!",
    "cohortAuditLog(cohortId: String!): [CohortAuditEntry!]!",
]

NEW_MUTATION_FIELDS = [
    "createCohort(input: CreateCohortInput!): CohortType!",
    "addStudentToCohort(cohortId: String!, loginName: String!): AddStudentResult!",
    "removeStudentFromCohort(cohortId: String!, studentId: String!): "
    "CohortMembershipResult!",
    "assignStaffToCohort(cohortId: String!, staffId: String!): CohortType!",
    "createAssignment(input: CreateAssignmentInput!): AssignmentType!",
    "startAssignmentAttempt(assignmentId: String!): SessionType!",
]


def test_new_types_present_in_snapshot():
    sdl = SNAPSHOT.read_text()
    for block in NEW_TYPES:
        assert block in sdl, f"missing new type block: {block}"


def test_new_fields_present():
    sdl = SNAPSHOT.read_text()
    for line in NEW_QUERY_FIELDS + NEW_MUTATION_FIELDS:
        assert line in sdl, f"missing additive field: {line}"


def test_snapshot_in_sync_with_live_schema():
    assert print_schema(schema) + "\n" == SNAPSHOT.read_text()
