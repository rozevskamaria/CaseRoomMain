import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MockedProvider } from "@apollo/client/testing";
import { GraphQLError } from "graphql";
import { I18nextProvider } from "react-i18next";
import { describe, expect, it, vi } from "vitest";
import i18n from "../../../i18n";
import {
  AuthorCasesQuery,
  CaseDraftQuery,
  PreviewCaseQuery,
  PublishCaseVersionMutation,
  SetCaseDraftLabDataMutation,
  SetCaseDraftLocalizationMutation,
  SetCaseDraftScalarsMutation,
} from "../../../graphql/authoringOperations";
import { CasesView } from "./CasesView";
import { CaseEditor } from "./CaseEditor";
import { CasePreview } from "./CasePreview";

const REUSE = { maxUsageCount: 20 };

function publishedSummary() {
  return {
    __typename: "CaseSummaryType" as const,
    caseId: "c-1",
    slug: "xla",
    versionId: "pub-1",
    versionNo: 1,
    status: "published",
    isCurrent: true,
    difficulty: "adv",
    topic: "Antibody deficiency",
    targetDiagnosis: "XLA",
    iuis: "I",
    hasLv: false,
  };
}

function draftSummary() {
  return {
    __typename: "CaseSummaryType" as const,
    caseId: "c-2",
    slug: "scid",
    versionId: "draft-1",
    versionNo: 2,
    status: "draft",
    isCurrent: false,
    difficulty: "adv",
    topic: "Combined immunodeficiency",
    targetDiagnosis: "SCID",
    iuis: "II",
    hasLv: true,
  };
}

function draftVersion(overrides: Record<string, unknown> = {}) {
  return {
    __typename: "CaseVersionType" as const,
    caseId: "c-2",
    slug: "scid",
    versionId: "draft-1",
    versionNo: 2,
    status: "draft",
    isCurrent: false,
    difficulty: "adv",
    topic: "Combined immunodeficiency",
    targetDiagnosis: "SCID",
    iuis: "II",
    localizations: [
      {
        __typename: "CaseLocalizationType" as const,
        language: "en",
        content: {
          title: "A Baby With Persistent Thrush",
          patient: "Baby, 5 months",
          topic: "Combined immunodeficiency",
          opening_clinical: "Failure to thrive",
          opening: "A worried parent arrives.",
          parent_prompt: "You are the parent.",
          exam_findings: "Oral thrush, no tonsils.",
          model_diagnosis: "SCID",
          model_management: "HSCT",
          model_genetic_counselling: "X-linked",
          red_flags: ["persistent thrush"],
          key_clues: ["low lymphocytes"],
          wrong_paths: {},
          lab_data: { CBC: "Lymphocytes: 0.4 ↓. NOTE: severely reduced." },
        },
      },
    ],
    tests: [
      { __typename: "CaseTestType" as const, key: "CBC", kind: "numeric_panel", ord: 0 },
    ],
    ...overrides,
  };
}

function renderWithMocks(ui: React.ReactElement, mocks: unknown[]) {
  void i18n.changeLanguage("en");
  return render(
    <I18nextProvider i18n={i18n}>
      <MockedProvider mocks={mocks as never}>{ui}</MockedProvider>
    </I18nextProvider>,
  );
}

describe("CasesView", () => {
  it("renders drafts and published groups for staff/admin", async () => {
    const mocks = [
      {
        ...REUSE,
        request: { query: AuthorCasesQuery },
        result: {
          data: {
            __typename: "Query",
            authorCases: [publishedSummary(), draftSummary()],
          },
        },
      },
    ];
    renderWithMocks(<CasesView onOpenDraft={() => {}} />, mocks);

    expect(await screen.findByText("scid")).toBeInTheDocument();
    expect(screen.getByText("xla")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Drafts" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Published" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Edit →" })).toBeInTheDocument();
  });
});

describe("CaseEditor", () => {
  it("edits scalars, prose and lab rows and saves via the right mutations", async () => {
    const scalarsCalled = vi.fn();
    const localizationCalled = vi.fn();
    const labDataCalled = vi.fn();

    const mocks = [
      {
        ...REUSE,
        request: { query: CaseDraftQuery, variables: { versionId: "draft-1" } },
        result: { data: { __typename: "Query", caseDraft: draftVersion() } },
      },
      {
        ...REUSE,
        request: { query: SetCaseDraftScalarsMutation },
        variableMatcher: (vars: { versionId: string }) => vars.versionId === "draft-1",
        result: () => {
          scalarsCalled();
          return { data: { __typename: "Mutation", setCaseDraftScalars: draftVersion() } };
        },
      },
      ...(["en", "lv"] as const).flatMap((lang) => [
        {
          ...REUSE,
          request: { query: SetCaseDraftLocalizationMutation },
          variableMatcher: (vars: { versionId: string; language: string }) =>
            vars.versionId === "draft-1" && vars.language === lang,
          result: () => {
            localizationCalled(lang);
            return {
              data: { __typename: "Mutation", setCaseDraftLocalization: draftVersion() },
            };
          },
        },
        {
          ...REUSE,
          request: { query: SetCaseDraftLabDataMutation },
          variableMatcher: (vars: { input: { versionId: string; language: string } }) =>
            vars.input.versionId === "draft-1" && vars.input.language === lang,
          result: () => {
            labDataCalled(lang);
            return {
              data: { __typename: "Mutation", setCaseDraftLabData: draftVersion() },
            };
          },
        },
      ]),
    ];

    renderWithMocks(
      <CaseEditor versionId="draft-1" canPublish onDiscarded={() => {}} />,
      mocks,
    );

    const titleInput = (await screen.findByDisplayValue(
      "A Baby With Persistent Thrush",
    )) as HTMLInputElement;
    fireEvent.change(titleInput, { target: { value: "Edited title" } });

    expect(screen.getByDisplayValue("Lymphocytes: 0.4 ↓. NOTE: severely reduced.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(labDataCalled).toHaveBeenCalledWith("lv"));
    expect(scalarsCalled).toHaveBeenCalled();
    expect(localizationCalled).toHaveBeenCalledWith("en");
    expect(localizationCalled).toHaveBeenCalledWith("lv");
    expect(labDataCalled).toHaveBeenCalledWith("en");
  });

  it("Copy from EN copies EN prose into LV without any network/AI call", async () => {
    const fetchSpy = vi.fn();
    const originalFetch = globalThis.fetch;
    globalThis.fetch = ((...args: unknown[]) => {
      fetchSpy(...args);
      return Promise.reject(new Error("network blocked"));
    }) as typeof fetch;

    try {
      const mocks = [
        {
          ...REUSE,
          request: { query: CaseDraftQuery, variables: { versionId: "draft-1" } },
          result: { data: { __typename: "Query", caseDraft: draftVersion() } },
        },
      ];
      renderWithMocks(
        <CaseEditor versionId="draft-1" canPublish onDiscarded={() => {}} />,
        mocks,
      );

      await screen.findByDisplayValue("A Baby With Persistent Thrush");

      fireEvent.click(screen.getByRole("button", { name: "Latviešu" }));
      expect(
        screen.queryByDisplayValue("A Baby With Persistent Thrush"),
      ).not.toBeInTheDocument();

      fireEvent.click(screen.getByRole("button", { name: "Copy from EN" }));

      expect(
        await screen.findByDisplayValue("A Baby With Persistent Thrush"),
      ).toBeInTheDocument();
      expect(fetchSpy).not.toHaveBeenCalled();
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("surfaces a backend validation error on publish", async () => {
    const mocks = [
      {
        ...REUSE,
        request: { query: CaseDraftQuery, variables: { versionId: "draft-1" } },
        result: { data: { __typename: "Query", caseDraft: draftVersion() } },
      },
      {
        ...REUSE,
        request: {
          query: PublishCaseVersionMutation,
          variables: { versionId: "draft-1" },
        },
        result: {
          errors: [new GraphQLError("incomplete_localization: missing model_diagnosis")],
        },
      },
    ];

    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    try {
      renderWithMocks(
        <CaseEditor versionId="draft-1" canPublish onDiscarded={() => {}} />,
        mocks,
      );
      await screen.findByDisplayValue("A Baby With Persistent Thrush");
      fireEvent.click(screen.getByRole("button", { name: "Publish" }));

      expect(
        await screen.findByText(/incomplete_localization: missing model_diagnosis/),
      ).toBeInTheDocument();
    } finally {
      confirmSpy.mockRestore();
    }
  });
});

describe("CasePreview", () => {
  it("renders a lab_data row through the runtime LabResultCard (arrows/flags resolve)", async () => {
    const mocks = [
      {
        ...REUSE,
        request: {
          query: PreviewCaseQuery,
          variables: { versionId: "draft-1", language: "en" },
        },
        result: {
          data: {
            __typename: "Query",
            previewCase: {
              __typename: "CasePreviewType",
              id: "scid",
              title: "A Baby With Persistent Thrush",
              topic: "Combined immunodeficiency",
              patient: "Baby, 5 months",
              difficulty: "adv",
              openingClinical: "Failure to thrive",
              opening: "A worried parent arrives.",
              targetDiagnosis: "SCID",
              targetIuis: "II",
              redFlags: ["persistent thrush"],
              parentPrompt: "You are the parent.",
              labData: { CBC: "Lymphocytes: 0.4 ↓. NOTE: severely reduced." },
              examFindings: "Oral thrush, no tonsils.",
              modelDiagnosis: "SCID",
              modelManagement: "HSCT",
              modelGeneticCounselling: "X-linked",
              keyClues: ["low lymphocytes"],
              wrongPaths: {},
            },
          },
        },
      },
    ];

    renderWithMocks(<CasePreview versionId="draft-1" language="en" />, mocks);

    expect(await screen.findByText("CBC")).toBeInTheDocument();
    expect(screen.getByText("Lymphocytes")).toBeInTheDocument();
    expect(screen.getByText(/severely reduced/)).toBeInTheDocument();
    expect(screen.getByText("↓")).toBeInTheDocument();
  });
});
