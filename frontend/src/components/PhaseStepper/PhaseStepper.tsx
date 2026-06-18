import type { CSSProperties } from "react";
import styles from "./PhaseStepper.module.css";

export interface PhaseStepperItem {
  key: string;
  label: string;
}

export interface PhaseStepperProps {
  phases: PhaseStepperItem[];
  currentPhase: string;
  style?: CSSProperties;
  className?: string;
}

export function PhaseStepper({
  phases,
  currentPhase,
  style,
  className,
}: PhaseStepperProps) {
  const classes = [styles.phaseBar, className].filter(Boolean).join(" ");
  const phaseIdx = phases.findIndex((p) => p.key === currentPhase);
  return (
    <div className={classes} style={style}>
      {phases.map((p, i) => {
        const active = currentPhase === p.key;
        const done = i < phaseIdx;
        const itemClasses = [
          styles.phaseItem,
          active ? styles.active : null,
          done ? styles.done : null,
        ]
          .filter(Boolean)
          .join(" ");
        return (
          <div key={p.key} className={itemClasses}>
            {done ? "✓ " : ""}
            {p.label}
          </div>
        );
      })}
    </div>
  );
}
