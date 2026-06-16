import { describe, it, expect, expectTypeOf } from "vitest";
import type { ResultOf, VariablesOf } from "@graphql-typed-document-node/core";
import {
  CaseQuery,
  SessionQuery,
  StartCaseMutation,
  SendMessageMutation,
  RequestExamMutation,
  SendTestOrderMutation,
  SetSummaryMutation,
  SubmitSummaryMutation,
  SetDifferentialsMutation,
  SubmitDifferentialsMutation,
  SetInterpretationMutation,
  SubmitInterpretationMutation,
  SetFinalAnswerFieldMutation,
  SubmitFinalAnswerMutation,
  RequestHintMutation,
  SubmitReflectionMutation,
  GoToSummaryMutation,
  ProposeDifferentialsMutation,
  InterpretResultsMutation,
  SubmitFinalMutation,
  OrderInvestigationsMutation,
  SessionFieldsFragment,
} from "./operations";

const documents = {
  CaseQuery,
  SessionQuery,
  StartCaseMutation,
  SendMessageMutation,
  RequestExamMutation,
  SendTestOrderMutation,
  SetSummaryMutation,
  SubmitSummaryMutation,
  SetDifferentialsMutation,
  SubmitDifferentialsMutation,
  SetInterpretationMutation,
  SubmitInterpretationMutation,
  SetFinalAnswerFieldMutation,
  SubmitFinalAnswerMutation,
  RequestHintMutation,
  SubmitReflectionMutation,
  GoToSummaryMutation,
  ProposeDifferentialsMutation,
  InterpretResultsMutation,
  SubmitFinalMutation,
  OrderInvestigationsMutation,
  SessionFieldsFragment,
};

describe("graphql operations", () => {
  it("exports a parsed document for every Phase 1 operation", () => {
    for (const [name, doc] of Object.entries(documents)) {
      expect(doc, name).toBeTruthy();
      expect((doc as { kind: string }).kind, name).toBe("Document");
    }
  });

  it("types the session selection the UI needs", () => {
    expectTypeOf<ResultOf<typeof StartCaseMutation>["startCase"]>().toMatchTypeOf<{
      id: string;
      phase: string;
      mode: string;
      hintsUsed: number;
      examDone: boolean;
      orderedTests: string[];
    }>();
  });

  it("types feedback scores when present", () => {
    type Feedback = NonNullable<ResultOf<typeof SessionQuery>["session"]>["feedback"];
    expectTypeOf<NonNullable<Feedback>["scores"]>().toMatchTypeOf<
      | {
          historyTaking: string;
          examination: string;
          differential: string;
          testSelection: string;
          interpretation: string;
          management: string;
        }
      | null
      | undefined
    >();
  });

  it("types message variants and ordered tests", () => {
    type Session = NonNullable<ResultOf<typeof SessionQuery>["session"]>;
    expectTypeOf<Session["messages"]>().toMatchTypeOf<
      Array<{ id: string; type: string; text: string }>
    >();
    expectTypeOf<Session["interpResult"]>().toEqualTypeOf<string>();
    expectTypeOf<Session["reflectionStep"]>().toEqualTypeOf<number>();
  });

  it("types operation variables", () => {
    expectTypeOf<VariablesOf<typeof CaseQuery>>().toMatchTypeOf<{ id: string }>();
    expectTypeOf<VariablesOf<typeof SendMessageMutation>>().toMatchTypeOf<{
      sessionId: string;
      text: string;
    }>();
    expectTypeOf<VariablesOf<typeof SetFinalAnswerFieldMutation>>().toMatchTypeOf<{
      sessionId: string;
      fieldName: string;
      value: string;
    }>();
  });

  it("types the send-message branch enum result", () => {
    expectTypeOf<
      ResultOf<typeof SendMessageMutation>["sendMessage"]["branch"]
    >().not.toBeNever();
  });
});
