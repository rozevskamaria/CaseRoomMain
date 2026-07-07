import { useTranslation } from "react-i18next";
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
  onSeeNext?: () => void;
  onReflect?: () => void;
  onBrowse?: () => void;
  showActions?: boolean;
}

export function FeedbackReport({
  feedback,
  caseTitle,
  mode,
  onSeeNext,
  onReflect,
  onBrowse,
  showActions = true,
}: FeedbackReportProps) {
  const { t } = useTranslation();
  return (
    <div className={styles.wrap}>
      <h2 className={styles.title}>{t("feedback.title")}</h2>
      <div className={styles.subtitle}>{caseTitle}</div>

      <AccuracyBanner
        accuracy={feedback.diagnosticAccuracy}
        comment={feedback.diagnosticComment}
      />

      <h3 className={styles.overviewHeading}>{t("feedback.overviewHeading")}</h3>
      <ScoreGrid scores={feedback.scores ?? {}} />

      <FeedbackList
        className={styles.wellDoneSection}
        title={t("feedback.wellDoneTitle")}
        items={feedback.wellDone ?? []}
        variant="strip"
        tone="teal"
      />

      {(feedback.missing ?? []).length > 0 && (
        <FeedbackList
          className={styles.section}
          title={t("feedback.areasToDevelopTitle")}
          items={feedback.missing}
          variant="strip"
          tone="amber"
        />
      )}

      <FeedbackList
        className={styles.section}
        title={t("feedback.keyCluesTitle")}
        items={feedback.keyClues ?? []}
        variant="boxedBullets"
        tone="navy"
      />

      <div className={styles.section}>
        <InfoBox
          title={t("feedback.reasoningTitle")}
          text={feedback.reasoningPathway}
          tone="surface"
        />
      </div>

      <div className={styles.twoColGrid}>
        <FeedbackList
          title={t("feedback.managementTitle")}
          items={feedback.managementPoints ?? []}
          variant="bareBullets"
          tone="navyLight"
        />
        <FeedbackList
          title={t("feedback.geneticTitle")}
          items={feedback.geneticPoints ?? []}
          variant="bareBullets"
          tone="teal"
        />
      </div>

      <div className={styles.section}>
        <InfoBox
          title={t("feedback.revisionTitle")}
          text={feedback.revisionTopic}
          tone="navyPale"
        />
      </div>

      {showActions && (
        <FeedbackActions
          mode={mode}
          onSeeNext={onSeeNext ?? (() => {})}
          onReflect={onReflect ?? (() => {})}
          onBrowse={onBrowse ?? (() => {})}
        />
      )}
    </div>
  );
}
