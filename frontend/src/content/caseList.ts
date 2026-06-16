export type Difficulty = "Beginner" | "Intermediate" | "Advanced";

export interface CaseMeta {
  id: string;
  title: string;
  patient: string;
  topic: string;
  difficulty: Difficulty;
}

export const CASE_LIST: CaseMeta[] = [
  {
    id: "xla",
    title: "A Boy Who Is Always Getting Pneumonia",
    patient: "2-year-old boy",
    topic: "Antibody Deficiency",
    difficulty: "Intermediate",
  },
  {
    id: "cgd",
    title: "Emils — A Toddler With Abscesses Everywhere",
    patient: "3-year-old boy",
    topic: "Phagocyte Defect",
    difficulty: "Advanced",
  },
  {
    id: "pfapa",
    title: "A Girl With Predictable Monthly Fevers",
    patient: "3-year-old girl",
    topic: "Autoinflammatory",
    difficulty: "Intermediate",
  },
  {
    id: "hies",
    title: "A Teenager Whose Eczema Never Responds to Treatment",
    patient: "13-year-old girl",
    topic: "Combined Immunodeficiency",
    difficulty: "Advanced",
  },
  {
    id: "scid",
    title: "A Baby With Infections After BCG Vaccination",
    patient: "Male infant, 2.5 months old",
    topic: "SCID / Combined Immunodeficiency",
    difficulty: "Advanced",
  },
  {
    id: "thi",
    title: "A Baby Referred for Low IgG",
    patient: "10-month-old boy (Toms)",
    topic: "Antibody Deficiency (Transient)",
    difficulty: "Beginner",
  },
];
