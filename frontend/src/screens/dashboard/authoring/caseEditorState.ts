export type EditorLang = "en" | "lv";

export const PROSE_FIELDS = [
  "title",
  "patient",
  "topic",
  "openingClinical",
  "opening",
  "parentPrompt",
  "examFindings",
  "modelDiagnosis",
  "modelManagement",
  "modelGeneticCounselling",
] as const;

export type ProseField = (typeof PROSE_FIELDS)[number];

export const LIST_FIELDS = ["redFlags", "keyClues"] as const;

export type ListField = (typeof LIST_FIELDS)[number];

export interface WrongPathRow {
  key: string;
  value: string;
}

export interface LangContent {
  title: string;
  patient: string;
  topic: string;
  openingClinical: string;
  opening: string;
  parentPrompt: string;
  examFindings: string;
  modelDiagnosis: string;
  modelManagement: string;
  modelGeneticCounselling: string;
  redFlags: string[];
  keyClues: string[];
  wrongPaths: WrongPathRow[];
}

export interface ScalarState {
  difficulty: string;
  targetDiagnosis: string;
  iuis: string;
}

export interface LabRow {
  key: string;
  kind: string;
  resultByLang: Record<EditorLang, string>;
}

export interface EditorState {
  versionId: string;
  slug: string;
  status: string;
  versionNo: number;
  scalars: ScalarState;
  byLang: Record<EditorLang, LangContent>;
  labRows: LabRow[];
  dirty: boolean;
}

export type EditorAction =
  | { type: "HYDRATE"; state: EditorState }
  | { type: "SET_SCALAR"; field: keyof ScalarState; value: string }
  | { type: "SET_PROSE"; lang: EditorLang; field: ProseField; value: string }
  | { type: "SET_LIST_ITEM"; lang: EditorLang; field: ListField; index: number; value: string }
  | { type: "ADD_LIST_ITEM"; lang: EditorLang; field: ListField }
  | { type: "REMOVE_LIST_ITEM"; lang: EditorLang; field: ListField; index: number }
  | { type: "SET_WRONG_PATH_KEY"; lang: EditorLang; index: number; value: string }
  | { type: "SET_WRONG_PATH_VALUE"; lang: EditorLang; index: number; value: string }
  | { type: "ADD_WRONG_PATH"; lang: EditorLang }
  | { type: "REMOVE_WRONG_PATH"; lang: EditorLang; index: number }
  | { type: "COPY_FROM_EN" }
  | { type: "ADD_LAB_ROW" }
  | { type: "SET_LAB_KEY"; index: number; value: string }
  | { type: "SET_LAB_KIND"; index: number; value: string }
  | { type: "SET_LAB_RESULT"; index: number; lang: EditorLang; value: string }
  | { type: "REMOVE_LAB_ROW"; index: number }
  | { type: "MARK_SAVED" };

export const EMPTY_LANG_CONTENT: LangContent = {
  title: "",
  patient: "",
  topic: "",
  openingClinical: "",
  opening: "",
  parentPrompt: "",
  examFindings: "",
  modelDiagnosis: "",
  modelManagement: "",
  modelGeneticCounselling: "",
  redFlags: [],
  keyClues: [],
  wrongPaths: [],
};

export const LAB_KINDS = [
  "numeric_panel",
  "imaging",
  "microbiology",
  "genetic",
  "qualitative",
] as const;

export type LabKind = (typeof LAB_KINDS)[number];

export function emptyEditorState(): EditorState {
  return {
    versionId: "",
    slug: "",
    status: "draft",
    versionNo: 1,
    scalars: { difficulty: "", targetDiagnosis: "", iuis: "" },
    byLang: {
      en: structuredClone(EMPTY_LANG_CONTENT),
      lv: structuredClone(EMPTY_LANG_CONTENT),
    },
    labRows: [],
    dirty: false,
  };
}

function dirty<T extends EditorState>(next: T): T {
  return { ...next, dirty: true };
}

export function editorReducer(state: EditorState, action: EditorAction): EditorState {
  switch (action.type) {
    case "HYDRATE":
      return action.state;
    case "MARK_SAVED":
      return { ...state, dirty: false };
    case "SET_SCALAR":
      return dirty({
        ...state,
        scalars: { ...state.scalars, [action.field]: action.value },
      });
    case "SET_PROSE": {
      const lang = state.byLang[action.lang];
      return dirty({
        ...state,
        byLang: {
          ...state.byLang,
          [action.lang]: { ...lang, [action.field]: action.value },
        },
      });
    }
    case "SET_LIST_ITEM": {
      const lang = state.byLang[action.lang];
      const items = lang[action.field].slice();
      items[action.index] = action.value;
      return dirty({
        ...state,
        byLang: {
          ...state.byLang,
          [action.lang]: { ...lang, [action.field]: items },
        },
      });
    }
    case "ADD_LIST_ITEM": {
      const lang = state.byLang[action.lang];
      return dirty({
        ...state,
        byLang: {
          ...state.byLang,
          [action.lang]: { ...lang, [action.field]: [...lang[action.field], ""] },
        },
      });
    }
    case "REMOVE_LIST_ITEM": {
      const lang = state.byLang[action.lang];
      const items = lang[action.field].filter((_, i) => i !== action.index);
      return dirty({
        ...state,
        byLang: {
          ...state.byLang,
          [action.lang]: { ...lang, [action.field]: items },
        },
      });
    }
    case "SET_WRONG_PATH_KEY": {
      const lang = state.byLang[action.lang];
      const rows = lang.wrongPaths.slice();
      rows[action.index] = { ...rows[action.index], key: action.value };
      return dirty({
        ...state,
        byLang: { ...state.byLang, [action.lang]: { ...lang, wrongPaths: rows } },
      });
    }
    case "SET_WRONG_PATH_VALUE": {
      const lang = state.byLang[action.lang];
      const rows = lang.wrongPaths.slice();
      rows[action.index] = { ...rows[action.index], value: action.value };
      return dirty({
        ...state,
        byLang: { ...state.byLang, [action.lang]: { ...lang, wrongPaths: rows } },
      });
    }
    case "ADD_WRONG_PATH": {
      const lang = state.byLang[action.lang];
      return dirty({
        ...state,
        byLang: {
          ...state.byLang,
          [action.lang]: { ...lang, wrongPaths: [...lang.wrongPaths, { key: "", value: "" }] },
        },
      });
    }
    case "REMOVE_WRONG_PATH": {
      const lang = state.byLang[action.lang];
      const rows = lang.wrongPaths.filter((_, i) => i !== action.index);
      return dirty({
        ...state,
        byLang: { ...state.byLang, [action.lang]: { ...lang, wrongPaths: rows } },
      });
    }
    case "COPY_FROM_EN":
      return dirty({
        ...state,
        byLang: {
          ...state.byLang,
          lv: structuredClone(state.byLang.en),
        },
      });
    case "ADD_LAB_ROW":
      return dirty({
        ...state,
        labRows: [...state.labRows, { key: "", kind: "numeric_panel", resultByLang: { en: "", lv: "" } }],
      });
    case "SET_LAB_KEY": {
      const rows = state.labRows.slice();
      rows[action.index] = { ...rows[action.index], key: action.value };
      return dirty({ ...state, labRows: rows });
    }
    case "SET_LAB_KIND": {
      const rows = state.labRows.slice();
      rows[action.index] = { ...rows[action.index], kind: action.value };
      return dirty({ ...state, labRows: rows });
    }
    case "SET_LAB_RESULT": {
      const rows = state.labRows.slice();
      const row = rows[action.index];
      rows[action.index] = {
        ...row,
        resultByLang: { ...row.resultByLang, [action.lang]: action.value },
      };
      return dirty({ ...state, labRows: rows });
    }
    case "REMOVE_LAB_ROW":
      return dirty({
        ...state,
        labRows: state.labRows.filter((_, i) => i !== action.index),
      });
    default:
      return state;
  }
}
