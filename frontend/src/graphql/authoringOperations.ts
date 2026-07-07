import { graphql } from "../gql";

export const CaseSummaryFieldsFragment = graphql(`
  fragment CaseSummaryFields on CaseSummaryType {
    caseId
    slug
    versionId
    versionNo
    status
    isCurrent
    difficulty
    topic
    targetDiagnosis
    iuis
    hasLv
  }
`);

export const CaseVersionFieldsFragment = graphql(`
  fragment CaseVersionFields on CaseVersionType {
    caseId
    slug
    versionId
    versionNo
    status
    isCurrent
    difficulty
    topic
    targetDiagnosis
    iuis
    localizations {
      language
      content
    }
    tests {
      key
      kind
      ord
    }
  }
`);

export const AuthorCasesQuery = graphql(`
  query AuthorCases {
    authorCases {
      ...CaseSummaryFields
    }
  }
`);

export const CaseDraftQuery = graphql(`
  query CaseDraft($versionId: String!) {
    caseDraft(versionId: $versionId) {
      ...CaseVersionFields
    }
  }
`);

export const PreviewCaseQuery = graphql(`
  query PreviewCase($versionId: String!, $language: String!) {
    previewCase(versionId: $versionId, language: $language) {
      id
      title
      topic
      patient
      difficulty
      openingClinical
      opening
      targetDiagnosis
      targetIuis
      redFlags
      parentPrompt
      labData
      examFindings
      modelDiagnosis
      modelManagement
      modelGeneticCounselling
      keyClues
      wrongPaths
    }
  }
`);

export const CreateCaseDraftMutation = graphql(`
  mutation CreateCaseDraft($slug: String = null, $fromVersionId: String = null) {
    createCaseDraft(slug: $slug, fromVersionId: $fromVersionId) {
      ...CaseVersionFields
    }
  }
`);

export const SetCaseDraftScalarsMutation = graphql(`
  mutation SetCaseDraftScalars($versionId: String!, $input: DraftScalarsInput!) {
    setCaseDraftScalars(versionId: $versionId, input: $input) {
      ...CaseVersionFields
    }
  }
`);

export const SetCaseDraftLocalizationMutation = graphql(`
  mutation SetCaseDraftLocalization(
    $versionId: String!
    $language: String!
    $content: JSON!
  ) {
    setCaseDraftLocalization(
      versionId: $versionId
      language: $language
      content: $content
    ) {
      ...CaseVersionFields
    }
  }
`);

export const SetCaseDraftLabDataMutation = graphql(`
  mutation SetCaseDraftLabData($input: SetDraftLabDataInput!) {
    setCaseDraftLabData(input: $input) {
      ...CaseVersionFields
    }
  }
`);

export const PublishCaseVersionMutation = graphql(`
  mutation PublishCaseVersion($versionId: String!) {
    publishCaseVersion(versionId: $versionId) {
      version {
        ...CaseVersionFields
      }
    }
  }
`);

export const DiscardCaseDraftMutation = graphql(`
  mutation DiscardCaseDraft($versionId: String!) {
    discardCaseDraft(versionId: $versionId) {
      caseId
      deletedCase
    }
  }
`);
