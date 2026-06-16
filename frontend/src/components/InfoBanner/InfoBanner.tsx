import type { CSSProperties, ReactNode } from "react";
import styles from "./InfoBanner.module.css";

export type InfoBannerTone = "teal" | "navy";

export interface InfoBannerProps {
  tone: InfoBannerTone;
  message: ReactNode;
  action?: ReactNode;
  style?: CSSProperties;
  className?: string;
}

export function InfoBanner({
  tone,
  message,
  action,
  style,
  className,
}: InfoBannerProps) {
  const classes = [styles.banner, styles[tone], className]
    .filter(Boolean)
    .join(" ");
  return (
    <div className={classes} style={style}>
      <div className={styles.message}>{message}</div>
      {action}
    </div>
  );
}
