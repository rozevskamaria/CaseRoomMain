import type { CSSProperties, ReactNode } from "react";
import styles from "./Pill.module.css";

export type PillTone = "difficulty" | "count" | "score" | "labFlag";

export type DifficultyValue = "adv" | "int" | "beg";
export type ScoreValue = "Excellent" | "Good" | "Developing" | string;

export interface PillProps {
  tone: PillTone;
  value?: DifficultyValue | ScoreValue;
  children?: ReactNode;
  style?: CSSProperties;
  className?: string;
}

function difficultyClass(value?: string): string {
  if (value === "adv") return styles.difficultyAdv;
  if (value === "int") return styles.difficultyInt;
  return styles.difficultyBeg;
}

function scoreClass(value?: string): string {
  if (value === "Excellent") return styles.scoreExcellent;
  if (value === "Good") return styles.scoreGood;
  if (value === "Developing") return styles.scoreDeveloping;
  return styles.scoreOther;
}

export function Pill({ tone, value, children, style, className }: PillProps) {
  const toneClasses: string[] = [];
  if (tone === "difficulty") {
    toneClasses.push(styles.difficulty, difficultyClass(value));
  } else if (tone === "count") {
    toneClasses.push(styles.count);
  } else if (tone === "score") {
    toneClasses.push(styles.score, scoreClass(value));
  } else {
    toneClasses.push(styles.labFlag);
  }
  const classes = [...toneClasses, className].filter(Boolean).join(" ");
  return (
    <span className={classes} style={style}>
      {children}
    </span>
  );
}
