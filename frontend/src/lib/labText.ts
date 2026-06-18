export type LabNote = { type: "note"; text: string };
export type LabRow = { type: "row"; param: string; value: string };
export type LabLine = LabNote | LabRow;

export function parseLabText(text: string): LabLine[] {
  const raw = text
    .replace(/\. NOTE:/gi, "\nNOTE:")
    .replace(/\. ⚠/g, "\n⚠")
    .replace(/\. KEY:/gi, "\nKEY:")
    .split(/\.\s+(?=[A-Z])/)
    .map((s) => s.trim().replace(/\.$/, "").trim())
    .filter(Boolean);

  return raw.map((sentence): LabLine => {
    if (/^(NOTE|⚠|KEY|IMPORTANT|WARNING)[:!]/i.test(sentence)) {
      return {
        type: "note",
        text: sentence.replace(/^(NOTE|⚠|KEY|IMPORTANT|WARNING)[:!]\s*/i, ""),
      };
    }
    const colonIdx = sentence.indexOf(":");
    if (colonIdx > 0 && colonIdx < 60) {
      return {
        type: "row",
        param: sentence.substring(0, colonIdx).trim(),
        value: sentence.substring(colonIdx + 1).trim(),
      };
    }
    const m = sentence.match(/^([A-Za-z][A-Za-z0-9+\-/\s]{0,35}?)\s+([<>≤≥~]?[\d.,]+.*)$/);
    if (m) {
      return { type: "row", param: m[1].trim(), value: m[2].trim() };
    }
    return { type: "note", text: sentence };
  });
}

export function flagRow(value: string): string {
  const v = value.toUpperCase();
  if (/↑↑↑|CRITICALLY/.test(v)) return "crit";
  if (/↑↑|MARKEDLY ELEVATED/.test(v)) return "hi2";
  if (/↑|ELEVATED|HIGH|POSITIVE(?! FOR)|RAISED/.test(v)) return "hi";
  if (/ABSENT|UNDETECTABLE|0\.0%|VIRTUALLY ABSENT/.test(v)) return "absent";
  if (/DIAGNOSTIC|PATHOGNOMONIC/.test(v)) return "diag";
  if (/↓↓↓|SEVERELY (LOW|DECREASED)|CRITICALLY LOW/.test(v)) return "lo3";
  if (/↓↓|MARKEDLY (LOW|DECREASED)/.test(v)) return "lo2";
  if (/↓|LOW|DECREASED|BELOW REFERENCE/.test(v)) return "lo";
  if (/NORMAL|NEGATIVE|NO GROWTH|NO PATHOGEN|NO SIGNIFICANT|INTACT|PRESENT AND NORMAL/.test(v)) return "ok";
  return "neutral";
}

export function formatLabText(testName: string, resultText: string): string {
  return `__LAB__${testName}\n${resultText}`;
}
