import type { CSSProperties, MouseEventHandler, ReactNode } from "react";
import styles from "./Card.module.css";

export type CardTone = "default" | "teal" | "amber" | "navy" | "red";

export interface CardProps {
  tone?: CardTone;
  borderColor?: string;
  style?: CSSProperties;
  className?: string;
  onClick?: MouseEventHandler<HTMLDivElement>;
  children?: ReactNode;
}

export function Card({
  tone = "default",
  borderColor,
  style,
  className,
  onClick,
  children,
}: CardProps) {
  const classes = [styles.card, styles[tone], className]
    .filter(Boolean)
    .join(" ");
  const mergedStyle: CSSProperties = borderColor
    ? { borderColor, ...style }
    : style ?? {};
  return (
    <div className={classes} style={mergedStyle} onClick={onClick}>
      {children}
    </div>
  );
}
