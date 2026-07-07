import { render, screen, within } from "@testing-library/react";
import { MockedProvider } from "@apollo/client/testing";
import type { MockedResponse } from "@apollo/client/testing";
import { describe, expect, it } from "vitest";
import { CohortAnalyticsPanel } from "./CohortAnalyticsPanel";
import type { CohortAnalyticsQuery as CohortAnalyticsQueryType } from "../../../gql/graphql";
import { CohortAnalyticsQuery } from "../../../graphql/cohortOperations";
import "../../../i18n";

const COHORT_ID = "c-1";

const populated: CohortAnalyticsQueryType = {
  __typename: "Query",
  cohortAnalytics: {
    __typename: "CohortAnalyticsType",
    cohortId: COHORT_ID,
    totalAttempts: 20,
    completedAttempts: 15,
    completionRate: 0.75,
    attemptsPerCase: { xla: 9, cgd: 7, pfapa: 4 },
    scoreDistribution: {
      historyTaking: { Excellent: 6, Good: 5, Developing: 3, "Needs review": 1 },
      examination: { Excellent: 4, Good: 6, Developing: 4, "Needs review": 1 },
      differential: { Excellent: 3, Good: 4, Developing: 6, "Needs review": 2 },
      testSelection: { Excellent: 5, Good: 5, Developing: 4, "Needs review": 1 },
      interpretation: { Excellent: 2, Good: 5, Developing: 6, "Needs review": 2 },
      management: { Excellent: 4, Good: 4, Developing: 5, "Needs review": 2 },
    },
    diagnosticAccuracyDistribution: {
      correct: 9,
      partially_correct: 4,
      incorrect: 2,
    },
    wrongPathFrequency: {
      "ordered-genetics-too-early": 5,
      "missed-neutropenia": 8,
      "anchored-on-allergy": 2,
    },
  },
};

const empty: CohortAnalyticsQueryType = {
  __typename: "Query",
  cohortAnalytics: {
    __typename: "CohortAnalyticsType",
    cohortId: COHORT_ID,
    totalAttempts: 0,
    completedAttempts: 0,
    completionRate: 0,
    attemptsPerCase: {},
    scoreDistribution: {},
    diagnosticAccuracyDistribution: {
      correct: 0,
      partially_correct: 0,
      incorrect: 0,
    },
    wrongPathFrequency: {},
  },
};

function mockFor(data: CohortAnalyticsQueryType): MockedResponse {
  return {
    request: { query: CohortAnalyticsQuery, variables: { cohortId: COHORT_ID } },
    result: { data },
  };
}

function renderPanel(data: CohortAnalyticsQueryType) {
  return render(
    <MockedProvider mocks={[mockFor(data)]}>
      <CohortAnalyticsPanel cohortId={COHORT_ID} />
    </MockedProvider>,
  );
}

describe("CohortAnalyticsPanel", () => {
  it("renders completion %, score-distribution bars, accuracy, attempts-per-case and wrong-path tables", async () => {
    renderPanel(populated);

    expect(await screen.findByText("75%")).toBeInTheDocument();
    expect(
      screen.getByText("15 of 20 attempts completed"),
    ).toBeInTheDocument();

    const progressbar = screen.getByRole("progressbar");
    expect(progressbar).toHaveAttribute("aria-valuenow", "75");

    expect(
      screen.getByText("Score distribution by rubric dimension"),
    ).toBeInTheDocument();
    expect(screen.getByText("history Taking")).toBeInTheDocument();
    expect(screen.getByText("management")).toBeInTheDocument();

    expect(screen.getByText("Attempts per case")).toBeInTheDocument();
    const caseCell = screen.getByText("A Boy Who Is Always Getting Pneumonia");
    expect(caseCell).toBeInTheDocument();
    const caseRow = caseCell.closest("tr") as HTMLElement;
    expect(within(caseRow).getByText("9")).toBeInTheDocument();

    expect(screen.getByText("Common wrong paths")).toBeInTheDocument();
    const wrongCell = screen.getByText("missed-neutropenia");
    const wrongRow = wrongCell.closest("tr") as HTMLElement;
    expect(within(wrongRow).getByText("8")).toBeInTheDocument();

    expect(screen.getByText("Diagnostic accuracy")).toBeInTheDocument();
    expect(screen.getByText("Partially correct")).toBeInTheDocument();
  });

  it("shows a friendly empty state when there are no attempts", async () => {
    renderPanel(empty);

    expect(await screen.findByText("No attempts yet")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Analytics will appear here once students in this cohort start completing cases.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });
});
