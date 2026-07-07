import { readSeenCases, resetSeenCases, writeSeenCase } from "./seenCases";
import { readLocale } from "../i18n/useLocale";
import type { Locale } from "../i18n/types";

export type Screen = "welcome" | "chat" | "reflection_done";
export type Mode = "practice" | "exam" | "reflection";
export type ActiveTab = "consultation" | "investigations" | "diagnosis";
export type InputMode = "history" | "summary_input" | "diff_input" | "interp_input";

export interface UiState {
  screen: Screen;
  mode: Mode;
  language: Locale;
  selectedCaseId: string | null;
  sessionId: string | null;
  activeTab: ActiveTab;
  inputMode: InputMode;
  showHintMenu: boolean;
  hintPopup: string | null;
  showFinalForm: boolean;
  showBrowse: boolean;
  busy: boolean;
  seenCases: string[];
}

export function createInitialUiState(): UiState {
  return {
    screen: "welcome",
    mode: "practice",
    language: readLocale(),
    selectedCaseId: null,
    sessionId: null,
    activeTab: "consultation",
    inputMode: "history",
    showHintMenu: false,
    hintPopup: null,
    showFinalForm: false,
    showBrowse: false,
    busy: false,
    seenCases: readSeenCases(),
  };
}

export const initialUiState: UiState = createInitialUiState();

export type UiAction =
  | { type: "SET_MODE"; mode: Mode }
  | { type: "SET_LANGUAGE"; language: Locale }
  | { type: "SET_SHOW_BROWSE"; value: boolean }
  | { type: "MARK_CASE_SEEN"; caseId: string }
  | { type: "RESET_PROGRESS" }
  | { type: "START_CASE"; caseId: string; sessionId: string | null }
  | { type: "SET_SESSION_ID"; sessionId: string | null }
  | { type: "SET_ACTIVE_TAB"; tab: ActiveTab }
  | { type: "SET_INPUT_MODE"; inputMode: InputMode }
  | { type: "ENTER_SUMMARY_INPUT" }
  | { type: "ENTER_DIFF_INPUT" }
  | { type: "ENTER_INTERP_INPUT" }
  | { type: "OPEN_FINAL_FORM"; tab?: ActiveTab }
  | { type: "SET_SHOW_FINAL_FORM"; value: boolean }
  | { type: "SET_SHOW_HINT_MENU"; value: boolean }
  | { type: "SET_HINT_POPUP"; value: string | null }
  | { type: "SET_BUSY"; value: boolean }
  | { type: "ENTER_REFLECTION" }
  | { type: "REFLECTION_DONE" }
  | { type: "RETURN_TO_WELCOME" };

export function uiReducer(state: UiState, action: UiAction): UiState {
  switch (action.type) {
    case "SET_MODE":
      return { ...state, mode: action.mode };

    case "SET_LANGUAGE":
      return { ...state, language: action.language };

    case "SET_SHOW_BROWSE":
      return { ...state, showBrowse: action.value };

    case "MARK_CASE_SEEN":
      return { ...state, seenCases: writeSeenCase(action.caseId, state.seenCases) };

    case "RESET_PROGRESS":
      resetSeenCases();
      return { ...state, seenCases: [] };

    case "START_CASE":
      return {
        ...state,
        screen: "chat",
        selectedCaseId: action.caseId,
        sessionId: action.sessionId,
        activeTab: "consultation",
        inputMode: "history",
        showHintMenu: false,
        hintPopup: null,
        showFinalForm: false,
        showBrowse: false,
        busy: false,
      };

    case "SET_SESSION_ID":
      return { ...state, sessionId: action.sessionId };

    case "SET_ACTIVE_TAB":
      return { ...state, activeTab: action.tab };

    case "SET_INPUT_MODE":
      return { ...state, inputMode: action.inputMode };

    case "ENTER_SUMMARY_INPUT":
      return { ...state, inputMode: "summary_input", activeTab: "consultation" };

    case "ENTER_DIFF_INPUT":
      return { ...state, inputMode: "diff_input", activeTab: "consultation" };

    case "ENTER_INTERP_INPUT":
      return { ...state, inputMode: "interp_input" };

    case "OPEN_FINAL_FORM":
      return {
        ...state,
        showFinalForm: true,
        activeTab: action.tab ?? state.activeTab,
      };

    case "SET_SHOW_FINAL_FORM":
      return { ...state, showFinalForm: action.value };

    case "SET_SHOW_HINT_MENU":
      return { ...state, showHintMenu: action.value };

    case "SET_HINT_POPUP":
      return { ...state, hintPopup: action.value };

    case "SET_BUSY":
      return { ...state, busy: action.value };

    case "ENTER_REFLECTION":
      return { ...state, mode: "reflection", activeTab: "consultation", inputMode: "history" };

    case "REFLECTION_DONE":
      return { ...state, screen: "reflection_done", busy: false };

    case "RETURN_TO_WELCOME":
      return {
        ...state,
        screen: "welcome",
        selectedCaseId: null,
        sessionId: null,
        activeTab: "consultation",
        inputMode: "history",
        showHintMenu: false,
        hintPopup: null,
        showFinalForm: false,
        busy: false,
      };

    default:
      return state;
  }
}
