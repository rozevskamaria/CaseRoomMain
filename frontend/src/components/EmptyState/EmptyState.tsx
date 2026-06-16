import type { CSSProperties, ReactNode } from "react";
import styles from "./EmptyState.module.css";

export interface EmptyStateProps {
  icon: ReactNode;
  title: ReactNode;
  description: ReactNode;
  action?: ReactNode;
  style?: CSSProperties;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  style,
  className,
}: EmptyStateProps) {
  const classes = [styles.emptyState, className].filter(Boolean).join(" ");
  return (
    <div className={classes} style={style}>
      <div className={styles.icon}>{icon}</div>
      <div className={styles.title}>{title}</div>
      <div className={styles.description}>{description}</div>
      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
}
