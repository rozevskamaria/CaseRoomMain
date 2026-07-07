import {
  EMPTY_LANG_CONTENT,
  type EditorLang,
  type EditorState,
  type LabRow,
  type LangContent,
  type WrongPathRow,
} from "./caseEditorState";

type RawContent = Record<string, unknown>;

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => (typeof item === "string" ? item : String(item)));
}

function asWrongPaths(value: unknown): WrongPathRow[] {
  if (value === null || typeof value !== "object") return [];
  return Object.entries(value as Record<string, unknown>).map(([key, v]) => ({
    key,
    value: typeof v === "string" ? v : String(v),
  }));
}

function contentFromRaw(raw: RawContent | undefined): LangContent {
  if (!raw) return structuredClone(EMPTY_LANG_CONTENT);
  return {
    title: asString(raw.title),
    patient: asString(raw.patient),
    topic: asString(raw.topic),
    openingClinical: asString(raw.opening_clinical),
    opening: asString(raw.opening),
    parentPrompt: asString(raw.parent_prompt),
    examFindings: asString(raw.exam_findings),
    modelDiagnosis: asString(raw.model_diagnosis),
    modelManagement: asString(raw.model_management),
    modelGeneticCounselling: asString(raw.model_genetic_counselling),
    redFlags: asStringList(raw.red_flags),
    keyClues: asStringList(raw.key_clues),
    wrongPaths: asWrongPaths(raw.wrong_paths),
  };
}

function labDataFromRaw(raw: RawContent | undefined): Record<string, string> {
  const out: Record<string, string> = {};
  const labData = raw?.lab_data;
  if (labData && typeof labData === "object") {
    for (const [key, value] of Object.entries(labData as Record<string, unknown>)) {
      out[key] = typeof value === "string" ? value : String(value);
    }
  }
  return out;
}

export interface PlainCaseVersion {
  caseId: string;
  slug: string;
  versionId: string;
  versionNo: number;
  status: string;
  isCurrent: boolean;
  difficulty: string;
  topic: string;
  targetDiagnosis: string;
  iuis: string;
  localizations: { language: string; content: unknown }[];
  tests: { key: string; kind: string; ord: number }[];
}

export function hydrateEditorState(version: PlainCaseVersion): EditorState {
  const byRawContent: Partial<Record<EditorLang, RawContent>> = {};
  for (const loc of version.localizations) {
    if (loc.language === "en" || loc.language === "lv") {
      byRawContent[loc.language] = (loc.content ?? {}) as RawContent;
    }
  }

  const enLab = labDataFromRaw(byRawContent.en);
  const lvLab = labDataFromRaw(byRawContent.lv);

  const orderedKeys: string[] = [];
  const sortedTests = [...version.tests].sort((a, b) => a.ord - b.ord);
  const kindByKey = new Map<string, string>();
  for (const test of sortedTests) {
    orderedKeys.push(test.key);
    kindByKey.set(test.key, test.kind);
  }
  for (const key of Object.keys(enLab)) {
    if (!orderedKeys.includes(key)) orderedKeys.push(key);
  }

  const labRows: LabRow[] = orderedKeys.map((key) => ({
    key,
    kind: kindByKey.get(key) ?? "numeric_panel",
    resultByLang: { en: enLab[key] ?? "", lv: lvLab[key] ?? "" },
  }));

  return {
    versionId: version.versionId,
    slug: version.slug,
    status: version.status,
    versionNo: version.versionNo,
    scalars: {
      difficulty: version.difficulty,
      targetDiagnosis: version.targetDiagnosis,
      iuis: version.iuis,
    },
    byLang: {
      en: contentFromRaw(byRawContent.en),
      lv: contentFromRaw(byRawContent.lv),
    },
    labRows,
    dirty: false,
  };
}

export function localizationContent(
  content: LangContent,
  labRows: LabRow[],
  lang: EditorLang,
): Record<string, unknown> {
  const labData: Record<string, string> = {};
  for (const row of labRows) {
    if (row.key.trim()) labData[row.key.trim()] = row.resultByLang[lang];
  }
  const wrongPaths: Record<string, string> = {};
  for (const wp of content.wrongPaths) {
    if (wp.key.trim()) wrongPaths[wp.key.trim()] = wp.value;
  }
  return {
    title: content.title,
    patient: content.patient,
    topic: content.topic,
    opening_clinical: content.openingClinical,
    opening: content.opening,
    parent_prompt: content.parentPrompt,
    exam_findings: content.examFindings,
    model_diagnosis: content.modelDiagnosis,
    model_management: content.modelManagement,
    model_genetic_counselling: content.modelGeneticCounselling,
    red_flags: content.redFlags,
    key_clues: content.keyClues,
    wrong_paths: wrongPaths,
    lab_data: labData,
  };
}

export function labTestsInput(
  labRows: LabRow[],
  lang: EditorLang,
): { key: string; kind: string; resultByLanguage: Record<string, string> }[] {
  return labRows
    .filter((row) => row.key.trim())
    .map((row) => ({
      key: row.key.trim(),
      kind: row.kind,
      resultByLanguage: { [lang]: row.resultByLang[lang] },
    }));
}
