export const SEEN_CASES_KEY = "iei_seen_cases";

export function readSeenCases(): string[] {
  try {
    const stored = localStorage.getItem(SEEN_CASES_KEY);
    return stored ? (JSON.parse(stored) as string[]) : [];
  } catch {
    return [];
  }
}

export function writeSeenCase(caseId: string, currentSeen: string[]): string[] {
  const updated = [...new Set([...currentSeen, caseId])];
  try {
    localStorage.setItem(SEEN_CASES_KEY, JSON.stringify(updated));
  } catch {
    return updated;
  }
  return updated;
}

export function resetSeenCases(): void {
  try {
    localStorage.removeItem(SEEN_CASES_KEY);
  } catch {
    return;
  }
}
