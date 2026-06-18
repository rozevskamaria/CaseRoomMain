import { vi } from "vitest";
import type {
  CaseMeta,
  ChatCallbacks,
  ChatUi,
  Session,
  SessionMessage,
} from "./types";

export function makeMessage(
  type: string,
  text: string,
  id = `${type}-${Math.random()}`,
): SessionMessage {
  return { __typename: "MessageType", id, type, text };
}

export function makeSession(overrides: Partial<Session> = {}): Session {
  return {
    __typename: "SessionType",
    id: "s1",
    caseId: "xla",
    phase: "history",
    mode: "practice",
    hintsUsed: 0,
    examDone: false,
    summary: "",
    differentials: "",
    interpText: "",
    interpResult: "",
    reflectionStep: 0,
    orderedTests: [],
    messages: [],
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
    ...overrides,
  };
}

export function makeUi(overrides: Partial<ChatUi> = {}): ChatUi {
  return {
    mode: "practice",
    activeTab: "consultation",
    inputMode: "history",
    input: "",
    showHintMenu: false,
    hintPopup: null,
    showFinalForm: false,
    busy: false,
    ...overrides,
  };
}

export const caseMeta: CaseMeta = {
  title: "A Boy Who Is Always Getting Pneumonia",
  patient: "2-year-old boy",
  topic: "Antibody Deficiency",
};

export function makeCallbacks(): ChatCallbacks {
  return {
    onSend: vi.fn(),
    onOrderTests: vi.fn(),
    onRequestExam: vi.fn(),
    onSubmitSummary: vi.fn(),
    onSubmitDifferentials: vi.fn(),
    onSubmitInterpretation: vi.fn(),
    onSubmitFinalAnswer: vi.fn(),
    onRequestHint: vi.fn(),
    onGetHint: vi.fn(),
    onSubmitReflection: vi.fn(),
    onSetTab: vi.fn(),
    onSetInputMode: vi.fn(),
    onShowHintMenu: vi.fn(),
    onCloseHintPopup: vi.fn(),
    onShowFinalForm: vi.fn(),
    onExit: vi.fn(),
    onSeeNext: vi.fn(),
    onReflect: vi.fn(),
    onBrowse: vi.fn(),
    onSetInput: vi.fn(),
    onSetSummary: vi.fn(),
    onSetDifferentials: vi.fn(),
    onSetInterpText: vi.fn(),
    onSetFinalAnswerField: vi.fn(),
    proposeDifferentials: vi.fn(),
    interpretResults: vi.fn(),
    submitFinal: vi.fn(),
    orderInvestigations: vi.fn(),
    goToSummary: vi.fn(),
  };
}

export function parentMessages(n: number): SessionMessage[] {
  return Array.from({ length: n }, (_, i) =>
    makeMessage("parent", `parent ${i}`, `parent-${i}`),
  );
}
