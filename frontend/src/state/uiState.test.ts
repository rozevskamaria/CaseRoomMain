import { beforeEach, describe, expect, it } from "vitest";
import {
  createInitialUiState,
  uiReducer,
  type UiState,
} from "./uiState";
import {
  SEEN_CASES_KEY,
  readSeenCases,
  resetSeenCases,
  writeSeenCase,
} from "./seenCases";

function dirtyState(): UiState {
  return {
    screen: "chat",
    mode: "exam",
    selectedCaseId: "xla",
    sessionId: "sess-1",
    activeTab: "diagnosis",
    inputMode: "interp_input",
    showHintMenu: true,
    hintPopup: "a hint",
    showFinalForm: true,
    showBrowse: true,
    busy: true,
    seenCases: ["xla", "cgd"],
  };
}

describe("createInitialUiState", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("matches the JSX initial client state", () => {
    const state = createInitialUiState();
    expect(state).toEqual({
      screen: "welcome",
      mode: "practice",
      selectedCaseId: null,
      sessionId: null,
      activeTab: "consultation",
      inputMode: "history",
      showHintMenu: false,
      hintPopup: null,
      showFinalForm: false,
      showBrowse: false,
      busy: false,
      seenCases: [],
    });
  });

  it("hydrates seenCases from localStorage", () => {
    localStorage.setItem(SEEN_CASES_KEY, JSON.stringify(["scid", "thi"]));
    expect(createInitialUiState().seenCases).toEqual(["scid", "thi"]);
  });
});

describe("uiReducer", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("SET_MODE sets the session mode", () => {
    const next = uiReducer(createInitialUiState(), { type: "SET_MODE", mode: "exam" });
    expect(next.mode).toBe("exam");
  });

  it("SET_SHOW_BROWSE toggles the browse list", () => {
    const next = uiReducer(createInitialUiState(), { type: "SET_SHOW_BROWSE", value: true });
    expect(next.showBrowse).toBe(true);
  });

  it("MARK_CASE_SEEN dedupes and persists to localStorage", () => {
    const start = { ...createInitialUiState(), seenCases: ["xla"] };
    const next = uiReducer(start, { type: "MARK_CASE_SEEN", caseId: "cgd" });
    expect(next.seenCases).toEqual(["xla", "cgd"]);
    expect(JSON.parse(localStorage.getItem(SEEN_CASES_KEY) as string)).toEqual(["xla", "cgd"]);

    const again = uiReducer(next, { type: "MARK_CASE_SEEN", caseId: "xla" });
    expect(again.seenCases).toEqual(["xla", "cgd"]);
  });

  it("RESET_PROGRESS clears seenCases and removes the localStorage key", () => {
    localStorage.setItem(SEEN_CASES_KEY, JSON.stringify(["xla", "cgd"]));
    const start = { ...createInitialUiState(), seenCases: ["xla", "cgd"] };
    const next = uiReducer(start, { type: "RESET_PROGRESS" });
    expect(next.seenCases).toEqual([]);
    expect(localStorage.getItem(SEEN_CASES_KEY)).toBeNull();
  });

  it("START_CASE moves to chat and resets client state without touching mode", () => {
    const start = { ...dirtyState(), screen: "welcome" as const };
    const next = uiReducer(start, { type: "START_CASE", caseId: "pfapa", sessionId: "sess-9" });
    expect(next.screen).toBe("chat");
    expect(next.selectedCaseId).toBe("pfapa");
    expect(next.sessionId).toBe("sess-9");
    expect(next.activeTab).toBe("consultation");
    expect(next.inputMode).toBe("history");
    expect(next.showHintMenu).toBe(false);
    expect(next.hintPopup).toBeNull();
    expect(next.showFinalForm).toBe(false);
    expect(next.showBrowse).toBe(false);
    expect(next.busy).toBe(false);
    expect(next.mode).toBe("exam");
    expect(next.seenCases).toEqual(["xla", "cgd"]);
  });

  it("SET_SESSION_ID stores the server session id", () => {
    const next = uiReducer(createInitialUiState(), { type: "SET_SESSION_ID", sessionId: "abc" });
    expect(next.sessionId).toBe("abc");
  });

  it("SET_ACTIVE_TAB switches tabs", () => {
    const next = uiReducer(createInitialUiState(), { type: "SET_ACTIVE_TAB", tab: "investigations" });
    expect(next.activeTab).toBe("investigations");
  });

  it("SET_INPUT_MODE switches input mode", () => {
    const next = uiReducer(createInitialUiState(), { type: "SET_INPUT_MODE", inputMode: "diff_input" });
    expect(next.inputMode).toBe("diff_input");
  });

  it("ENTER_SUMMARY_INPUT sets summary input on the consultation tab", () => {
    const start = { ...createInitialUiState(), activeTab: "investigations" as const };
    const next = uiReducer(start, { type: "ENTER_SUMMARY_INPUT" });
    expect(next.inputMode).toBe("summary_input");
    expect(next.activeTab).toBe("consultation");
  });

  it("ENTER_DIFF_INPUT sets diff input on the consultation tab", () => {
    const start = { ...createInitialUiState(), activeTab: "investigations" as const };
    const next = uiReducer(start, { type: "ENTER_DIFF_INPUT" });
    expect(next.inputMode).toBe("diff_input");
    expect(next.activeTab).toBe("consultation");
  });

  it("ENTER_INTERP_INPUT sets interp input without changing the tab", () => {
    const start = { ...createInitialUiState(), activeTab: "investigations" as const };
    const next = uiReducer(start, { type: "ENTER_INTERP_INPUT" });
    expect(next.inputMode).toBe("interp_input");
    expect(next.activeTab).toBe("investigations");
  });

  it("OPEN_FINAL_FORM opens the form and can move to the diagnosis tab", () => {
    const withTab = uiReducer(createInitialUiState(), { type: "OPEN_FINAL_FORM", tab: "diagnosis" });
    expect(withTab.showFinalForm).toBe(true);
    expect(withTab.activeTab).toBe("diagnosis");

    const start = { ...createInitialUiState(), activeTab: "diagnosis" as const };
    const withoutTab = uiReducer(start, { type: "OPEN_FINAL_FORM" });
    expect(withoutTab.showFinalForm).toBe(true);
    expect(withoutTab.activeTab).toBe("diagnosis");
  });

  it("SET_SHOW_FINAL_FORM toggles the final form flag", () => {
    const next = uiReducer(createInitialUiState(), { type: "SET_SHOW_FINAL_FORM", value: true });
    expect(next.showFinalForm).toBe(true);
  });

  it("SET_SHOW_HINT_MENU toggles the hint menu", () => {
    const next = uiReducer(createInitialUiState(), { type: "SET_SHOW_HINT_MENU", value: true });
    expect(next.showHintMenu).toBe(true);
  });

  it("SET_HINT_POPUP sets and clears the hint popup", () => {
    const opened = uiReducer(createInitialUiState(), { type: "SET_HINT_POPUP", value: "think compartment" });
    expect(opened.hintPopup).toBe("think compartment");
    const closed = uiReducer(opened, { type: "SET_HINT_POPUP", value: null });
    expect(closed.hintPopup).toBeNull();
  });

  it("SET_BUSY toggles busy", () => {
    const next = uiReducer(createInitialUiState(), { type: "SET_BUSY", value: true });
    expect(next.busy).toBe(true);
  });

  it("ENTER_REFLECTION sets reflection mode on the consultation tab", () => {
    const start = { ...dirtyState() };
    const next = uiReducer(start, { type: "ENTER_REFLECTION" });
    expect(next.mode).toBe("reflection");
    expect(next.activeTab).toBe("consultation");
    expect(next.inputMode).toBe("history");
  });

  it("REFLECTION_DONE moves to the reflection_done screen and clears busy", () => {
    const start = { ...dirtyState(), busy: true };
    const next = uiReducer(start, { type: "REFLECTION_DONE" });
    expect(next.screen).toBe("reflection_done");
    expect(next.busy).toBe(false);
  });

  it("RETURN_TO_WELCOME resets client navigation without clearing seenCases or mode", () => {
    const start = { ...dirtyState() };
    const next = uiReducer(start, { type: "RETURN_TO_WELCOME" });
    expect(next.screen).toBe("welcome");
    expect(next.selectedCaseId).toBeNull();
    expect(next.sessionId).toBeNull();
    expect(next.activeTab).toBe("consultation");
    expect(next.inputMode).toBe("history");
    expect(next.showHintMenu).toBe(false);
    expect(next.hintPopup).toBeNull();
    expect(next.showFinalForm).toBe(false);
    expect(next.busy).toBe(false);
    expect(next.mode).toBe("exam");
    expect(next.seenCases).toEqual(["xla", "cgd"]);
  });
});

describe("seenCases storage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("readSeenCases returns [] when nothing is stored", () => {
    expect(readSeenCases()).toEqual([]);
  });

  it("readSeenCases parses a stored array", () => {
    localStorage.setItem(SEEN_CASES_KEY, JSON.stringify(["hies"]));
    expect(readSeenCases()).toEqual(["hies"]);
  });

  it("readSeenCases swallows malformed JSON and returns []", () => {
    localStorage.setItem(SEEN_CASES_KEY, "{not json");
    expect(readSeenCases()).toEqual([]);
  });

  it("writeSeenCase dedupes, persists, and returns the updated array", () => {
    const first = writeSeenCase("xla", []);
    expect(first).toEqual(["xla"]);
    const second = writeSeenCase("xla", first);
    expect(second).toEqual(["xla"]);
    const third = writeSeenCase("cgd", second);
    expect(third).toEqual(["xla", "cgd"]);
    expect(JSON.parse(localStorage.getItem(SEEN_CASES_KEY) as string)).toEqual(["xla", "cgd"]);
  });

  it("resetSeenCases removes the key", () => {
    localStorage.setItem(SEEN_CASES_KEY, JSON.stringify(["xla"]));
    resetSeenCases();
    expect(localStorage.getItem(SEEN_CASES_KEY)).toBeNull();
  });
});
