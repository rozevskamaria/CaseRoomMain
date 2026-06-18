export const PHASE_ORDER = [
  "history",
  "summary",
  "examination",
  "differential",
  "tests",
  "interpretation",
  "final",
  "feedback",
] as const;

export type Phase = (typeof PHASE_ORDER)[number];

export const PHASE_LABELS: Record<string, string> = {
  history: "History Taking",
  summary: "Clinical Summary",
  examination: "Physical Examination",
  differential: "Differential Diagnosis",
  tests: "Investigations",
  interpretation: "Interpretation",
  final: "Final Answer",
  feedback: "Feedback Report",
  reflection: "Reflection",
};

export const PHASE_STEPS = PHASE_ORDER.map((key) => ({
  key,
  label: PHASE_LABELS[key],
}));

export const REFLECTION_QS = [
  "What was your initial diagnosis when you first heard the case opening?",
  "Which specific finding or test result changed your thinking most significantly?",
  "Was there a moment where you felt uncertain or stuck? What helped you move forward?",
  "What would you do differently if you encountered this case again?",
  "What is the single most important clinical or scientific concept you will take away from this case?",
];
