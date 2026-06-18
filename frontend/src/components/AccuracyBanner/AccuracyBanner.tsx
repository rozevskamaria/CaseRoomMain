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

function headline(accuracy: DiagnosticAccuracy): string {
  if (accuracy === "correct") return "✓ Correct diagnosis";
  if (accuracy === "partially_correct") return "◐ Partially correct";
  return "○ Incorrect diagnosis";
}

export function AccuracyBanner({ accuracy, comment }: AccuracyBannerProps) {
  return (
    <div className={[styles.banner, toneClass(accuracy)].join(" ")}>
      <div className={styles.headline}>{headline(accuracy)}</div>
      <div className={styles.comment}>{comment}</div>
    </div>
  );
}
