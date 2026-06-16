import type { CSSProperties, ReactNode } from "react";
import styles from "./TypingIndicator.module.css";

export interface TypingIndicatorProps {
  label?: ReactNode;
  text: ReactNode;
  style?: CSSProperties;
  className?: string;
}

export function TypingIndicator({
  label,
  text,
  style,
  className,
}: TypingIndicatorProps) {
  if (!label) {
    const classes = [styles.centered, className].filter(Boolean).join(" ");
    return (
      <div className={classes} style={style}>
        {text}
      </div>
    );
  }
  const classes = [styles.row, className].filter(Boolean).join(" ");
  return (
    <div className={classes} style={style}>
      <div className={styles.bubble}>
        <div className={styles.label}>{label}</div>
        <div className={styles.body}>{text}</div>
      </div>
    </div>
  );
}
