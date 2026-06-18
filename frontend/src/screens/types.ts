import type { ChangeEvent } from "react";
import type { SessionFieldsFragment } from "../gql/graphql";
import type { ActiveTab, InputMode, Mode } from "../state/uiState";

export type Session = SessionFieldsFragment;
export type SessionMessage = Session["messages"][number];
export type FinalAnswerField =
  | "diagnosis"
  | "findings"
  | "differentials"
  | "tests"
  | "management"
  | "genetics"
  | "explanation";

export interface CaseMeta {
  title: string;
  patient: string;
  topic: string;
}

export interface ChatUi {
  mode: Mode;
  activeTab: ActiveTab;
  inputMode: InputMode;
  input: string;
  showHintMenu: boolean;
  hintPopup: string | null;
  showFinalForm: boolean;
  busy: boolean;
}

export interface ChatCallbacks {
  onSend: () => void;
  onOrderTests: () => void;
  onRequestExam: () => void;
  onSubmitSummary: () => void;
  onSubmitDifferentials: () => void;
  onSubmitInterpretation: () => void;
  onSubmitFinalAnswer: () => void;
  onRequestHint: () => void;
  onGetHint: () => void;
  onSubmitReflection: () => void;
  onSetTab: (tab: ActiveTab) => void;
  onSetInputMode: (mode: InputMode) => void;
  onShowHintMenu: (open: boolean) => void;
  onCloseHintPopup: () => void;
  onShowFinalForm: (open: boolean) => void;
  onExit: () => void;
  onSeeNext: () => void;
  onReflect: () => void;
  onBrowse: () => void;
  onSetInput: (value: string) => void;
  onSetSummary: (value: string) => void;
  onSetDifferentials: (value: string) => void;
  onSetInterpText: (value: string) => void;
  onSetFinalAnswerField: (field: FinalAnswerField, value: string) => void;
  proposeDifferentials: () => void;
  interpretResults: () => void;
  submitFinal: () => void;
  orderInvestigations: () => void;
  goToSummary: () => void;
}

export type TextAreaChange = ChangeEvent<HTMLTextAreaElement>;
export type InputChange = ChangeEvent<HTMLInputElement>;
