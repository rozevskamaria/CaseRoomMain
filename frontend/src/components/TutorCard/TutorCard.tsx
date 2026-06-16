import type { CSSProperties, ReactNode } from "react";
import styles from "./TutorCard.module.css";

export interface TutorCardProps {
  text: ReactNode;
  label?: ReactNode;
  style?: CSSProperties;
  className?: string;
}

export function TutorCard({
  text,
  label = "🎓 Clinical tutor",
  style,
  className,
}: TutorCardProps) {
  const classes = [styles.card, className].filter(Boolean).join(" ");
  return (
    <div className={classes} style={style}>
      <div className={styles.label}>{label}</div>
      <div className={styles.body}>{text}</div>
    </div>
  );
}
