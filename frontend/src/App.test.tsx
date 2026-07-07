import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MockedProvider } from "@apollo/client/testing";
import { afterEach, describe, expect, it } from "vitest";
import App from "./App";
import {
  CaseQuery,
  SessionQuery,
  StartCaseLocalizedMutation,
} from "./graphql/operations";
import { resetSeenCases } from "./state/seenCases";

const OPENING_TEXT =
  "Clinic note: a 2-year-old boy presents with recurrent pneumonia.";
const PARENT_TEXT = "He has been getting chest infections again and again.";

const sessionFields = {
  __typename: "SessionType" as const,
  id: "sess-1",
  caseId: "xla",
  phase: "history",
  mode: "practice",
  language: "en",
  hintsUsed: 0,
  examDone: false,
  summary: "",
  differentials: "",
  interpText: "",
  interpResult: "",
  reflectionStep: 0,
  orderedTests: [],
  messages: [
    { __typename: "MessageType" as const, id: "m1", type: "system", text: OPENING_TEXT },
    { __typename: "MessageType" as const, id: "m2", type: "parent", text: PARENT_TEXT },
  ],
  finalAnswer: {
    __typename: "FinalAnswerType" as const,
    diagnosis: "",
    findings: "",
    differentials: "",
    tests: "",
    management: "",
    genetics: "",
    explanation: "",
  },
  feedback: null,
};

const caseData = {
  __typename: "CaseType" as const,
  id: "xla",
  title: "A Boy Who Is Always Getting Pneumonia",
  topic: "Antibody Deficiency",
  patient: "2-year-old boy",
  difficulty: "Intermediate",
  openingClinical: OPENING_TEXT,
  opening: OPENING_TEXT,
  targetDiagnosis: "X-linked Agammaglobulinaemia (XLA)",
  targetIuis: "Predominantly antibody deficiencies",
};

const startMock = {
  request: {
    query: StartCaseLocalizedMutation,
    variables: { caseId: "xla", mode: "practice", language: "en" },
  },
  result: { data: { __typename: "Mutation", startCaseLocalized: sessionFields } },
};
const sessionMock = {
  request: { query: SessionQuery, variables: { id: "sess-1" } },
  result: { data: { __typename: "Query", session: sessionFields } },
};
const caseMock = {
  request: { query: CaseQuery, variables: { id: "xla" } },
  result: { data: { __typename: "Query", case: caseData } },
};

function buildMocks() {
  return [startMock, sessionMock, sessionMock, sessionMock, caseMock, caseMock, caseMock];
}

function openCase() {
  fireEvent.click(
    screen.getByRole("button", { name: /Browse cases individually/i }),
  );
  fireEvent.click(screen.getByText("A Boy Who Is Always Getting Pneumonia"));
}

afterEach(() => {
  resetSeenCases();
});

describe("App", () => {
  it("renders the welcome screen first", () => {
    render(
      <MockedProvider mocks={buildMocks()}>
        <App />
      </MockedProvider>,
    );
    expect(
      screen.getByRole("heading", { name: "Clinical Immunology" }),
    ).toBeInTheDocument();
  });

  it("starts a case and shows the chat screen with the opening message", async () => {
    render(
      <MockedProvider mocks={buildMocks()}>
        <App />
      </MockedProvider>,
    );

    openCase();

    expect(await screen.findByText(OPENING_TEXT)).toBeInTheDocument();
    expect(screen.getByText(PARENT_TEXT)).toBeInTheDocument();
    expect(
      screen.getByText("A Boy Who Is Always Getting Pneumonia"),
    ).toBeInTheDocument();
  });

  it("switches to the Investigations tab", async () => {
    render(
      <MockedProvider mocks={buildMocks()}>
        <App />
      </MockedProvider>,
    );

    openCase();
    await screen.findByText(OPENING_TEXT);

    fireEvent.click(screen.getByRole("button", { name: /Investigations/i }));

    await waitFor(() =>
      expect(
        screen.getByText("No investigations ordered yet"),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByPlaceholderText(/CBC, CRP, immunoglobulins/i),
    ).toBeInTheDocument();
  });
});
