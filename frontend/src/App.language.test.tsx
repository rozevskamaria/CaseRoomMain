import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MockedProvider } from "@apollo/client/testing";
import { afterEach, describe, expect, it } from "vitest";
import App from "./App";
import {
  CaseQuery,
  SessionQuery,
  StartCaseLocalizedMutation,
} from "./graphql/operations";
import i18n from "./i18n";
import { LOCALE_KEY } from "./i18n/useLocale";
import { resetSeenCases } from "./state/seenCases";

const OPENING_TEXT = "Klīniskā piezīme: zēns ar atkārtotu pneimoniju.";

const sessionFields = {
  __typename: "SessionType" as const,
  id: "sess-1",
  caseId: "xla",
  phase: "history",
  mode: "practice",
  language: "lv",
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

let localizedVariables: Record<string, unknown> | null = null;

const startMock = {
  request: {
    query: StartCaseLocalizedMutation,
    variables: { caseId: "xla", mode: "practice", language: "lv" },
  },
  result: () => {
    localizedVariables = { caseId: "xla", mode: "practice", language: "lv" };
    return { data: { __typename: "Mutation", startCaseLocalized: sessionFields } };
  },
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

afterEach(async () => {
  resetSeenCases();
  localStorage.removeItem(LOCALE_KEY);
  await i18n.changeLanguage("en");
  localizedVariables = null;
});

describe("App language selection", () => {
  it("starts a case via startCaseLocalized with the selected language", async () => {
    render(
      <MockedProvider mocks={buildMocks()}>
        <App />
      </MockedProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "LV" }));
    fireEvent.click(
      screen.getByRole("button", { name: /Pārlūkot gadījumus atsevišķi/i }),
    );
    fireEvent.click(screen.getByText("A Boy Who Is Always Getting Pneumonia"));

    expect(await screen.findByText(OPENING_TEXT)).toBeInTheDocument();
    await waitFor(() =>
      expect(localizedVariables).toEqual({
        caseId: "xla",
        mode: "practice",
        language: "lv",
      }),
    );
  });
});
