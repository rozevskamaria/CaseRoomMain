import { useQuery } from "@apollo/client";
import { useTranslation } from "react-i18next";
import { Card } from "../../../components/Card";
import { EmptyState } from "../../../components/EmptyState";
import { CohortAnalyticsQuery } from "../../../graphql/cohortOperations";
import { CASE_LIST } from "../../../content/caseList";
import { DashboardSpinner } from "../DashboardShell";
import styles from "./CohortAnalyticsPanel.module.css";

export type ScoreBand = "Excellent" | "Good" | "Developing" | "Needs review";

export type ScoreDistribution = Record<string, Record<string, number>>;
export type AttemptsPerCase = Record<string, number>;
export type DiagnosticAccuracy = Record<string, number>;
export type WrongPathFrequency = Record<string, number>;

const RUBRIC_DIMENSIONS = [
  "historyTaking",
  "examination",
  "differential",
  "testSelection",
  "interpretation",
  "management",
] as const;

const SCORE_BANDS: ScoreBand[] = [
  "Excellent",
  "Good",
  "Developing",
  "Needs review",
];

const BAND_CLASS: Record<ScoreBand, string> = {
  Excellent: styles.bandExcellent,
  Good: styles.bandGood,
  Developing: styles.bandDeveloping,
  "Needs review": styles.bandNeedsReview,
};

const ACCURACY_KEYS = ["correct", "partially_correct", "incorrect"] as const;

const ACCURACY_CLASS: Record<(typeof ACCURACY_KEYS)[number], string> = {
  correct: styles.accCorrect,
  partially_correct: styles.accPartial,
  incorrect: styles.accIncorrect,
};

export interface CohortAnalyticsPanelProps {
  cohortId: string;
}

function caseTitle(slug: string): string {
  return CASE_LIST.find((c) => c.id === slug)?.title ?? slug;
}

export function CohortAnalyticsPanel({ cohortId }: CohortAnalyticsPanelProps) {
  const { t } = useTranslation();
  const { data, loading } = useQuery(CohortAnalyticsQuery, {
    variables: { cohortId },
    fetchPolicy: "cache-and-network",
  });

  if (loading && data === undefined) {
    return <DashboardSpinner />;
  }

  const analytics = data?.cohortAnalytics;
  if (!analytics || analytics.totalAttempts === 0) {
    return (
      <EmptyState
        icon="📊"
        title={t("dashboard.analytics.emptyTitle")}
        description={t("dashboard.analytics.emptyDescription")}
      />
    );
  }

  const scoreDistribution = analytics.scoreDistribution as ScoreDistribution;
  const attemptsPerCase = analytics.attemptsPerCase as AttemptsPerCase;
  const accuracy =
    analytics.diagnosticAccuracyDistribution as DiagnosticAccuracy;
  const wrongPaths = analytics.wrongPathFrequency as WrongPathFrequency;

  const completionPct = Math.round(analytics.completionRate * 100);

  const caseRows = Object.entries(attemptsPerCase).sort((a, b) => b[1] - a[1]);
  const wrongPathRows = Object.entries(wrongPaths).sort((a, b) => b[1] - a[1]);
  const accuracyTotal = ACCURACY_KEYS.reduce(
    (sum, key) => sum + (accuracy[key] ?? 0),
    0,
  );

  return (
    <div className={styles.panel}>
      <Card className={styles.block}>
        <div className={styles.blockHeading}>
          {t("dashboard.analytics.completionHeading")}
        </div>
        <div className={styles.completionStat}>
          {t("dashboard.analytics.completionStat", {
            completed: analytics.completedAttempts,
            total: analytics.totalAttempts,
          })}
        </div>
        <div
          className={styles.progressTrack}
          role="progressbar"
          aria-valuenow={completionPct}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className={styles.progressFill}
            style={{ width: `${completionPct}%` }}
          />
        </div>
        <div className={styles.completionPct}>{completionPct}%</div>
      </Card>

      <Card className={styles.block}>
        <div className={styles.blockHeading}>
          {t("dashboard.analytics.scoreHeading")}
        </div>
        <div className={styles.legend}>
          {SCORE_BANDS.map((band) => (
            <span key={band} className={styles.legendItem}>
              <span className={`${styles.swatch} ${BAND_CLASS[band]}`} />
              {t(`dashboard.analytics.band.${band}` as "dashboard.analytics.band.Excellent")}
            </span>
          ))}
        </div>
        <div className={styles.dimList}>
          {RUBRIC_DIMENSIONS.map((dim) => {
            const counts = scoreDistribution[dim] ?? {};
            const total = SCORE_BANDS.reduce(
              (sum, band) => sum + (counts[band] ?? 0),
              0,
            );
            return (
              <div key={dim} className={styles.dimRow}>
                <span className={styles.dimLabel}>
                  {t(
                    `feedback.scoreDomain.${dim}` as "feedback.scoreDomain.examination",
                  )}
                </span>
                <div className={styles.stackedBar}>
                  {total === 0 ? (
                    <div className={styles.stackedEmpty} />
                  ) : (
                    SCORE_BANDS.map((band) => {
                      const count = counts[band] ?? 0;
                      if (count === 0) return null;
                      const pct = (count / total) * 100;
                      return (
                        <div
                          key={band}
                          className={`${styles.segment} ${BAND_CLASS[band]}`}
                          style={{ width: `${pct}%` }}
                          title={`${t(`dashboard.analytics.band.${band}` as "dashboard.analytics.band.Excellent")}: ${count}`}
                        >
                          {count}
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      <Card className={styles.block}>
        <div className={styles.blockHeading}>
          {t("dashboard.analytics.accuracyHeading")}
        </div>
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.th}>
                {t("dashboard.analytics.accuracyOutcome")}
              </th>
              <th className={`${styles.th} ${styles.thNum}`}>
                {t("dashboard.analytics.count")}
              </th>
            </tr>
          </thead>
          <tbody>
            {ACCURACY_KEYS.map((key) => {
              const count = accuracy[key] ?? 0;
              const pct =
                accuracyTotal === 0 ? 0 : (count / accuracyTotal) * 100;
              return (
                <tr key={key}>
                  <td className={styles.td}>
                    <div className={styles.accRow}>
                      <span className={styles.accLabel}>
                        {t(`dashboard.analytics.accuracy.${key}` as "dashboard.analytics.accuracy.correct")}
                      </span>
                      <div className={styles.accBarTrack}>
                        <div
                          className={`${styles.accBarFill} ${ACCURACY_CLASS[key]}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className={`${styles.td} ${styles.tdNum}`}>{count}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>

      <Card className={styles.block}>
        <div className={styles.blockHeading}>
          {t("dashboard.analytics.attemptsPerCaseHeading")}
        </div>
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.th}>
                {t("dashboard.analytics.caseColumn")}
              </th>
              <th className={`${styles.th} ${styles.thNum}`}>
                {t("dashboard.analytics.count")}
              </th>
            </tr>
          </thead>
          <tbody>
            {caseRows.map(([slug, count]) => (
              <tr key={slug}>
                <td className={styles.td}>{caseTitle(slug)}</td>
                <td className={`${styles.td} ${styles.tdNum}`}>{count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card className={styles.block}>
        <div className={styles.blockHeading}>
          {t("dashboard.analytics.wrongPathHeading")}
        </div>
        {wrongPathRows.length === 0 ? (
          <p className={styles.emptyText}>
            {t("dashboard.analytics.wrongPathEmpty")}
          </p>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th}>
                  {t("dashboard.analytics.wrongPathColumn")}
                </th>
                <th className={`${styles.th} ${styles.thNum}`}>
                  {t("dashboard.analytics.count")}
                </th>
              </tr>
            </thead>
            <tbody>
              {wrongPathRows.map(([key, count]) => (
                <tr key={key}>
                  <td className={styles.td}>{key}</td>
                  <td className={`${styles.td} ${styles.tdNum}`}>{count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
