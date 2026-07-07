import { useTranslation } from "react-i18next";
import styles from "./AccuracyBanner.module.css";

export type DiagnosticAccuracy = "correct" | "partially_correct" | "incorrect";

export interface AccuracyBannerProps {
  accuracy: DiagnosticAccuracy;
  comment: string;
}

function toneClass(accuracy: DiagnosticAccuracy): string {
  if (accuracy === "correct") return styles.correct;
  if (accuracy === "partially_correct") return styles.partial;
  return styles.incorrect;
}

export function AccuracyBanner({ accuracy, comment }: AccuracyBannerProps) {
  const { t } = useTranslation();
  const headline =
    accuracy === "correct"
      ? t("feedback.accuracyCorrect")
      : accuracy === "partially_correct"
        ? t("feedback.accuracyPartial")
        : t("feedback.accuracyIncorrect");
  return (
    <div className={[styles.banner, toneClass(accuracy)].join(" ")}>
      <div className={styles.headline}>{headline}</div>
      <div className={styles.comment}>{comment}</div>
    </div>
  );
}
