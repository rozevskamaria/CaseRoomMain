import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MockedProvider } from "@apollo/client/testing";
import { describe, expect, it } from "vitest";
import { EducatorDashboard } from "./EducatorDashboard";
import type { Me } from "./EducatorDashboard";
import {
  AssignmentsForCohortQuery,
  CohortQuery,
  CohortRosterQuery,
  MyCohortsQuery,
  StudentAttemptsQuery,
} from "../../graphql/cohortOperations";
import { SessionQuery } from "../../graphql/operations";

const staffMe: Me = {
  __typename: "MeType",
  id: "s-1",
  role: "staff",
  status: "active",
  loginName: "100001",
  email: null,
  fullName: "Dr Staff",
};

const COHORT_ID = "c-1";
const STUDENT_ID = "u-1";
const ATTEMPT_ID = "att-1";

const REUSE = { maxUsageCount: 10 };

const cohortSummary = {
  __typename: "CohortType" as const,
  id: COHORT_ID,
  name: "Year 5 — Group A",
  academicYear: "2025/2026",
  archived: false,
  createdAt: "2026-01-01T00:00:00Z",
  studentCount: 1,
};

const mocks = [
  {
    ...REUSE,
    request: { query: MyCohortsQuery },
    result: { data: { __typename: "Query", myCohorts: [cohortSummary] } },
  },
  {
    ...REUSE,
    request: { query: CohortQuery, variables: { id: COHORT_ID } },
    result: {
      data: {
        __typename: "Query",
        cohort: { ...cohortSummary, staff: [] },
      },
    },
  },
  {
    ...REUSE,
    request: { query: CohortRosterQuery, variables: { cohortId: COHORT_ID } },
    result: {
      data: {
        __typename: "Query",
        cohortRoster: [
          {
            __typename: "CohortStudentType",
            cohortId: COHORT_ID,
            joinedAt: "2026-02-01T00:00:00Z",
            user: {
              __typename: "MeType",
              id: STUDENT_ID,
              role: "student",
              status: "active",
              loginName: "482913",
              email: null,
              fullName: "Anna Student",
            },
          },
        ],
      },
    },
  },
  {
    ...REUSE,
    request: {
      query: AssignmentsForCohortQuery,
      variables: { cohortId: COHORT_ID },
    },
    result: {
      data: { __typename: "Query", assignmentsForCohort: [] },
    },
  },
  {
    ...REUSE,
    request: {
      query: StudentAttemptsQuery,
      variables: { cohortId: COHORT_ID, studentId: STUDENT_ID },
    },
    result: {
      data: {
        __typename: "Query",
        studentAttempts: [
          {
            __typename: "AttemptType",
            id: ATTEMPT_ID,
            caseId: "xla",
            mode: "practice",
            phase: "feedback",
            status: "completed",
            startedAt: "2026-03-01T09:00:00Z",
            completedAt: "2026-03-01T10:00:00Z",
          },
        ],
      },
    },
  },
  {
    ...REUSE,
    request: { query: SessionQuery, variables: { id: ATTEMPT_ID } },
    result: {
      data: {
        __typename: "Query",
        session: {
          __typename: "SessionType",
          id: ATTEMPT_ID,
          caseId: "xla",
          phase: "feedback",
          mode: "practice",
          language: "en",
          hintsUsed: 0,
          examDone: true,
          summary: "",
          differentials: "",
          interpText: "",
          interpResult: "",
          reflectionStep: 0,
          orderedTests: ["CBC"],
          messages: [
            {
              __typename: "MessageType",
              id: "m1",
              type: "student",
              text: "When did the infections start?",
            },
            {
              __typename: "MessageType",
              id: "m2",
              type: "parent",
              text: "Around six months of age.",
            },
            {
              __typename: "MessageType",
              id: "m3",
              type: "lab",
              text: "CBC: low lymphocytes",
            },
          ],
          finalAnswer: {
            __typename: "FinalAnswerType",
            diagnosis: "",
            findings: "",
            differentials: "",
            tests: "",
            management: "",
            genetics: "",
            explanation: "",
          },
          feedback: null,
        },
      },
    },
  },
];

function renderDashboard() {
  return render(
    <MockedProvider mocks={mocks}>
      <EducatorDashboard me={staffMe} onLogout={() => {}} />
    </MockedProvider>,
  );
}

describe("EducatorDashboard", () => {
  it("navigates cohorts → roster → attempts → replay and back", async () => {
    renderDashboard();

    const cohort = await screen.findByText("Year 5 — Group A");
    fireEvent.click(cohort);

    const reviewButtons = await screen.findAllByRole("button", {
      name: "Review →",
    });
    expect(screen.getByText("Anna Student")).toBeInTheDocument();
    fireEvent.click(reviewButtons[0]);

    const attemptCard = await screen.findByText(
      "A Boy Who Is Always Getting Pneumonia",
    );
    expect(
      screen.getByText("Assignment-linked attempts for this student. Select one to review the transcript."),
    ).toBeInTheDocument();
    fireEvent.click(attemptCard);

    expect(
      await screen.findByText(
        "Read-only review — this is the transcript exactly as the student saw it. You cannot reply or change anything.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("When did the infections start?"),
    ).toBeInTheDocument();
    expect(screen.getByText("Around six months of age.")).toBeInTheDocument();

    const backButtons = screen.getAllByRole("button", { name: "← Back" });
    fireEvent.click(backButtons[0]);
    expect(
      await screen.findByText("A Boy Who Is Always Getting Pneumonia"),
    ).toBeInTheDocument();
  });

  it("renders the read-only investigations transcript via the lab tab", async () => {
    renderDashboard();
    fireEvent.click(await screen.findByText("Year 5 — Group A"));
    fireEvent.click((await screen.findAllByRole("button", { name: "Review →" }))[0]);
    fireEvent.click(
      await screen.findByText("A Boy Who Is Always Getting Pneumonia"),
    );

    await screen.findByText("When did the infections start?");
    fireEvent.click(screen.getByRole("button", { name: /Investigations/ }));
    await waitFor(() =>
      expect(screen.getByText("CBC: low lymphocytes")).toBeInTheDocument(),
    );
  });
});
