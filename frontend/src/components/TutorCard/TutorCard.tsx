import type { CSSProperties, ReactNode } from "react";
import { useTranslation } from "react-i18next";
import styles from "./TutorCard.module.css";

export interface TutorCardProps {
  text: ReactNode;
  label?: ReactNode;
  style?: CSSProperties;
  className?: string;
}

export function TutorCard({ text, label, style, className }: TutorCardProps) {
  const { t } = useTranslation();
  const classes = [styles.card, className].filter(Boolean).join(" ");
  return (
    <div className={classes} style={style}>
      <div className={styles.label}>{label ?? t("tutor.label")}</div>
      <div className={styles.body}>{text}</div>
    </div>
  );
}
