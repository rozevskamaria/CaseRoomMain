import { graphql } from "../gql";

export const CohortStudentFieldsFragment = graphql(`
  fragment CohortStudentFields on CohortStudentType {
    cohortId
    joinedAt
    user {
      id
      role
      status
      loginName
      email
      fullName
    }
  }
`);

export const AssignmentFieldsFragment = graphql(`
  fragment AssignmentFields on AssignmentType {
    id
    cohortId
    caseId
    caseVersionId
    title
    mode
    language
    opensAt
    dueAt
    createdAt
  }
`);

export const AttemptSummaryFieldsFragment = graphql(`
  fragment AttemptSummaryFields on AttemptType {
    id
    caseId
    mode
    phase
    status
    startedAt
    completedAt
  }
`);

export const CohortSummaryFieldsFragment = graphql(`
  fragment CohortSummaryFields on CohortType {
    id
    name
    academicYear
    archived
    createdAt
    studentCount
  }
`);

export const MyCohortsQuery = graphql(`
  query MyCohorts {
    myCohorts {
      ...CohortSummaryFields
    }
  }
`);

export const CohortQuery = graphql(`
  query Cohort($id: String!) {
    cohort(id: $id) {
      ...CohortSummaryFields
      staff {
        id
        role
        status
        loginName
        email
        fullName
      }
    }
  }
`);

export const CohortRosterQuery = graphql(`
  query CohortRoster($cohortId: String!) {
    cohortRoster(cohortId: $cohortId) {
      ...CohortStudentFields
    }
  }
`);

export const StudentAttemptsQuery = graphql(`
  query StudentAttempts($cohortId: String!, $studentId: String!) {
    studentAttempts(cohortId: $cohortId, studentId: $studentId) {
      ...AttemptSummaryFields
    }
  }
`);

export const AssignmentsForCohortQuery = graphql(`
  query AssignmentsForCohort($cohortId: String!) {
    assignmentsForCohort(cohortId: $cohortId) {
      ...AssignmentFields
    }
  }
`);

export const LookupStudentQuery = graphql(`
  query LookupStudent($cohortId: String!, $loginName: String!) {
    lookupStudent(cohortId: $cohortId, loginName: $loginName) {
      status
      fullName
    }
  }
`);

export const CohortAuditLogQuery = graphql(`
  query CohortAuditLog($cohortId: String!) {
    cohortAuditLog(cohortId: $cohortId) {
      id
      actorId
      subjectId
      action
      createdAt
    }
  }
`);

export const CohortAnalyticsQuery = graphql(`
  query CohortAnalytics($cohortId: String!) {
    cohortAnalytics(cohortId: $cohortId) {
      cohortId
      totalAttempts
      completedAttempts
      completionRate
      attemptsPerCase
      scoreDistribution
      diagnosticAccuracyDistribution
      wrongPathFrequency
    }
  }
`);

export const CreateCohortMutation = graphql(`
  mutation CreateCohort($input: CreateCohortInput!) {
    createCohort(input: $input) {
      ...CohortSummaryFields
    }
  }
`);

export const AddStudentToCohortMutation = graphql(`
  mutation AddStudentToCohort($cohortId: String!, $loginName: String!) {
    addStudentToCohort(cohortId: $cohortId, loginName: $loginName) {
      status
      cohort {
        id
        studentCount
      }
      student {
        id
        loginName
        fullName
      }
    }
  }
`);

export const RemoveStudentFromCohortMutation = graphql(`
  mutation RemoveStudentFromCohort($cohortId: String!, $studentId: String!) {
    removeStudentFromCohort(cohortId: $cohortId, studentId: $studentId) {
      cohort {
        id
        studentCount
      }
      student {
        id
        loginName
      }
    }
  }
`);

export const AssignStaffToCohortMutation = graphql(`
  mutation AssignStaffToCohort($cohortId: String!, $staffId: String!) {
    assignStaffToCohort(cohortId: $cohortId, staffId: $staffId) {
      id
      staff {
        id
        loginName
        fullName
      }
    }
  }
`);

export const CreateAssignmentMutation = graphql(`
  mutation CreateAssignment($input: CreateAssignmentInput!) {
    createAssignment(input: $input) {
      ...AssignmentFields
    }
  }
`);
