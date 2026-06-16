import type { CSSProperties, ReactNode } from "react";
import styles from "./ChatHeader.module.css";

export interface ChatHeaderProps {
  title: ReactNode;
  subtitle: ReactNode;
  rightSlot?: ReactNode;
  children?: ReactNode;
  style?: CSSProperties;
  className?: string;
}

export function ChatHeader({
  title,
  subtitle,
  rightSlot,
  children,
  style,
  className,
}: ChatHeaderProps) {
  const classes = [styles.chatTop, className].filter(Boolean).join(" ");
  const right = rightSlot ?? children;
  return (
    <div className={classes} style={style}>
      <div>
        <div className={styles.title}>{title}</div>
        <div className={styles.subtitle}>{subtitle}</div>
      </div>
      <div className={styles.rightSlot}>{right}</div>
    </div>
  );
}
