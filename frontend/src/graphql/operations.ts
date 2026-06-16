import { graphql } from "../gql";

export const SessionFieldsFragment = graphql(`
  fragment SessionFields on SessionType {
    id
    caseId
    phase
    mode
    hintsUsed
    examDone
    summary
    differentials
    interpText
    interpResult
    reflectionStep
    orderedTests
    messages {
      id
      type
      text
    }
    finalAnswer {
      diagnosis
      findings
      differentials
      tests
      management
      genetics
      explanation
    }
    feedback {
      diagnosticAccuracy
      diagnosticComment
      wellDone
      missing
      keyClues
      reasoningPathway
      managementPoints
      geneticPoints
      revisionTopic
      scores {
        historyTaking
        examination
        differential
        testSelection
        interpretation
        management
      }
    }
  }
`);

export const CaseQuery = graphql(`
  query Case($id: String!) {
    case(id: $id) {
      id
      title
      topic
      patient
      difficulty
      openingClinical
      opening
      targetDiagnosis
      targetIuis
    }
  }
`);

export const SessionQuery = graphql(`
  query Session($id: String!) {
    session(id: $id) {
      ...SessionFields
    }
  }
`);

export const StartCaseMutation = graphql(`
  mutation StartCase($caseId: String!, $mode: String!) {
    startCase(caseId: $caseId, mode: $mode) {
      ...SessionFields
    }
  }
`);

export const SendMessageMutation = graphql(`
  mutation SendMessage($sessionId: String!, $text: String!) {
    sendMessage(sessionId: $sessionId, text: $text) {
      branch
      session {
        ...SessionFields
      }
    }
  }
`);

export const RequestExamMutation = graphql(`
  mutation RequestExam($sessionId: String!) {
    requestExam(sessionId: $sessionId) {
      ...SessionFields
    }
  }
`);

export const SendTestOrderMutation = graphql(`
  mutation SendTestOrder($sessionId: String!, $text: String!) {
    sendTestOrder(sessionId: $sessionId, text: $text) {
      ...SessionFields
    }
  }
`);

export const SetSummaryMutation = graphql(`
  mutation SetSummary($sessionId: String!, $value: String!) {
    setSummary(sessionId: $sessionId, value: $value) {
      ...SessionFields
    }
  }
`);

export const SubmitSummaryMutation = graphql(`
  mutation SubmitSummary($sessionId: String!) {
    submitSummary(sessionId: $sessionId) {
      ...SessionFields
    }
  }
`);

export const SetDifferentialsMutation = graphql(`
  mutation SetDifferentials($sessionId: String!, $value: String!) {
    setDifferentials(sessionId: $sessionId, value: $value) {
      ...SessionFields
    }
  }
`);

export const SubmitDifferentialsMutation = graphql(`
  mutation SubmitDifferentials($sessionId: String!) {
    submitDifferentials(sessionId: $sessionId) {
      ...SessionFields
    }
  }
`);

export const SetInterpretationMutation = graphql(`
  mutation SetInterpretation($sessionId: String!, $value: String!) {
    setInterpretation(sessionId: $sessionId, value: $value) {
      ...SessionFields
    }
  }
`);

export const SubmitInterpretationMutation = graphql(`
  mutation SubmitInterpretation($sessionId: String!) {
    submitInterpretation(sessionId: $sessionId) {
      ...SessionFields
    }
  }
`);

export const SetFinalAnswerFieldMutation = graphql(`
  mutation SetFinalAnswerField($sessionId: String!, $fieldName: String!, $value: String!) {
    setFinalAnswerField(sessionId: $sessionId, fieldName: $fieldName, value: $value) {
      ...SessionFields
    }
  }
`);

export const SubmitFinalAnswerMutation = graphql(`
  mutation SubmitFinalAnswer($sessionId: String!, $answer: FinalAnswerInput) {
    submitFinalAnswer(sessionId: $sessionId, answer: $answer) {
      ...SessionFields
    }
  }
`);

export const RequestHintMutation = graphql(`
  mutation RequestHint($sessionId: String!) {
    requestHint(sessionId: $sessionId)
  }
`);

export const SubmitReflectionMutation = graphql(`
  mutation SubmitReflection($sessionId: String!, $text: String!) {
    submitReflection(sessionId: $sessionId, text: $text) {
      ...SessionFields
    }
  }
`);

export const GoToSummaryMutation = graphql(`
  mutation GoToSummary($sessionId: String!, $prompt: String!) {
    goToSummary(sessionId: $sessionId, prompt: $prompt) {
      ...SessionFields
    }
  }
`);

export const ProposeDifferentialsMutation = graphql(`
  mutation ProposeDifferentials($sessionId: String!, $prompt: String!) {
    proposeDifferentials(sessionId: $sessionId, prompt: $prompt) {
      ...SessionFields
    }
  }
`);

export const InterpretResultsMutation = graphql(`
  mutation InterpretResults($sessionId: String!, $prompt: String!) {
    interpretResults(sessionId: $sessionId, prompt: $prompt) {
      ...SessionFields
    }
  }
`);

export const SubmitFinalMutation = graphql(`
  mutation SubmitFinal($sessionId: String!, $prompt: String!) {
    submitFinal(sessionId: $sessionId, prompt: $prompt) {
      ...SessionFields
    }
  }
`);

export const OrderInvestigationsMutation = graphql(`
  mutation OrderInvestigations($sessionId: String!) {
    orderInvestigations(sessionId: $sessionId) {
      ...SessionFields
    }
  }
`);
