import { AccuracyBanner } from "../AccuracyBanner";
import type { DiagnosticAccuracy } from "../AccuracyBanner";
import { ScoreGrid } from "../ScoreGrid";
import { FeedbackList } from "../FeedbackList";
import { InfoBox } from "../InfoBox";
import { FeedbackActions } from "../FeedbackActions";
import styles from "./FeedbackReport.module.css";

export interface Feedback {
  diagnosticAccuracy: DiagnosticAccuracy;
  diagnosticComment: string;
  wellDone: string[];
  missing: string[];
  keyClues: string[];
  reasoningPathway: string;
  managementPoints: string[];
  geneticPoints: string[];
  revisionTopic: string;
  scores: Record<string, string>;
}

export interface FeedbackReportProps {
  feedback: Feedback;
  caseTitle: string;
  mode: string;
  onSeeNext: () => void;
  onReflect: () => void;
  onBrowse: () => void;
}

export function FeedbackReport({
  feedback,
  caseTitle,
  mode,
  onSeeNext,
  onReflect,
  onBrowse,
}: FeedbackReportProps) {
  return (
    <div className={styles.wrap}>
      <h2 className={styles.title}>Feedback Report</h2>
      <div className={styles.subtitle}>{caseTitle}</div>

      <AccuracyBanner
        accuracy={feedback.diagnosticAccuracy}
        comment={feedback.diagnosticComment}
      />

      <h3 className={styles.overviewHeading}>Performance overview</h3>
      <ScoreGrid scores={feedback.scores ?? {}} />

      <FeedbackList
        className={styles.wellDoneSection}
        title="✓ What you did well"
        items={feedback.wellDone ?? []}
        variant="strip"
        tone="teal"
      />

      {(feedback.missing ?? []).length > 0 && (
        <FeedbackList
          className={styles.section}
          title="◎ Areas to develop"
          items={feedback.missing}
          variant="strip"
          tone="amber"
        />
      )}

      <FeedbackList
        className={styles.section}
        title="🔍 Key diagnostic clues in this case"
        items={feedback.keyClues ?? []}
        variant="boxedBullets"
        tone="navy"
      />

      <div className={styles.section}>
        <InfoBox
          title="🧭 Ideal reasoning pathway"
          text={feedback.reasoningPathway}
          tone="surface"
        />
      </div>

      <div className={styles.twoColGrid}>
        <FeedbackList
          title="💊 Management learning points"
          items={feedback.managementPoints ?? []}
          variant="bareBullets"
          tone="navyLight"
        />
        <FeedbackList
          title="🧬 Genetic counselling points"
          items={feedback.geneticPoints ?? []}
          variant="bareBullets"
          tone="teal"
        />
      </div>

      <div className={styles.section}>
        <InfoBox
          title="📖 Suggested revision"
          text={feedback.revisionTopic}
          tone="navyPale"
        />
      </div>

      <FeedbackActions
        mode={mode}
        onSeeNext={onSeeNext}
        onReflect={onReflect}
        onBrowse={onBrowse}
      />
    </div>
  );
}
