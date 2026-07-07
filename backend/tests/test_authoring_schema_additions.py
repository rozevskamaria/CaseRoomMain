from __future__ import annotations

from pathlib import Path

SNAPSHOT = Path(__file__).parent / "schema.graphql"

ADDED_TYPES = (
    "type CaseSummaryType {",
    "type CaseVersionType {",
    "type CaseLocalizationType {",
    "type CaseTestType {",
    "type CasePreviewType {",
    "type PublishResultType {",
    "type DiscardDraftResult {",
    "input DraftScalarsInput {",
    "input LabTestInput {",
    "input SetDraftLabDataInput {",
    "scalar JSON",
)

ADDED_QUERY_FIELDS = (
    "authorCases: [CaseSummaryType!]!",
    "caseDraft(versionId: String!): CaseVersionType",
    'previewCase(versionId: String!, language: String! = "en"): CasePreviewType',
)

ADDED_MUTATION_FIELDS = (
    "createCaseDraft(slug: String = null, fromVersionId: String = null):"
    " CaseVersionType!",
    "setCaseDraftScalars(versionId: String!, input: DraftScalarsInput!):"
    " CaseVersionType!",
    "setCaseDraftLocalization(versionId: String!, language: String!, content:"
    " JSON!): CaseVersionType!",
    "setCaseDraftLabData(input: SetDraftLabDataInput!): CaseVersionType!",
    "publishCaseVersion(versionId: String!): PublishResultType!",
    "discardCaseDraft(versionId: String!): DiscardDraftResult!",
)


def test_authoring_contract_additions_present():
    sdl = SNAPSHOT.read_text()
    for fragment in ADDED_TYPES:
        assert fragment in sdl, f"missing additive type: {fragment}"
    for field in ADDED_QUERY_FIELDS:
        assert field in sdl, f"missing additive query field: {field}"
    for field in ADDED_MUTATION_FIELDS:
        assert field in sdl, f"missing additive mutation field: {field}"


def test_preview_type_mirrors_case_runtime_field_set():
    from app.api.graphql.schema import CasePreviewType
    from app.schemas.case import Case

    preview_fields = {
        f.name for f in CasePreviewType.__strawberry_definition__.fields
    }
    runtime_fields = set(Case.model_fields.keys())
    assert preview_fields == runtime_fields
