import type { CSSProperties, ReactNode } from "react";
import styles from "./Callout.module.css";

export type CalloutTone = "teal" | "amber";

export interface CalloutProps {
  tone: CalloutTone;
  style?: CSSProperties;
  className?: string;
  children?: ReactNode;
}

export function Callout({ tone, style, className, children }: CalloutProps) {
  const classes = [styles.callout, styles[tone], className]
    .filter(Boolean)
    .join(" ");
  return (
    <div className={classes} style={style}>
      {children}
    </div>
  );
}
