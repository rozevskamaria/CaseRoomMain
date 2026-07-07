import { useQuery } from "@apollo/client";
import { useTranslation } from "react-i18next";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { Pill } from "../../components/Pill";
import { CASE_LIST } from "../../content/caseList";
import { StudentAttemptsQuery } from "../../graphql/cohortOperations";
import { DashboardSpinner } from "./DashboardShell";
import styles from "./StudentReviewView.module.css";

export interface StudentReviewViewProps {
  cohortId: string;
  studentId: string;
  onSelectAttempt: (attemptId: string) => void;
}

function modeLabel(t: (key: string) => string, mode: string): string {
  if (mode === "practice") return t("chat.modePractice");
  if (mode === "exam") return t("chat.modeExam");
  if (mode === "reflection") return t("chat.modeReflection");
  return mode;
}

export function StudentReviewView({
  cohortId,
  studentId,
  onSelectAttempt,
}: StudentReviewViewProps) {
  const { t } = useTranslation();
  const { data, loading } = useQuery(StudentAttemptsQuery, {
    variables: { cohortId, studentId },
    fetchPolicy: "cache-and-network",
  });

  const attempts = data?.studentAttempts ?? [];

  if (loading && data === undefined) {
    return <DashboardSpinner />;
  }

  return (
    <div className={styles.view}>
      <h2 className={styles.heading}>{t("dashboard.attempts.heading")}</h2>
      <p className={styles.intro}>{t("dashboard.attempts.intro")}</p>

      {attempts.length === 0 ? (
        <EmptyState
          icon="📂"
          title={t("dashboard.attempts.emptyTitle")}
          description={t("dashboard.attempts.emptyDescription")}
        />
      ) : (
        <div className={styles.list}>
          {attempts.map((attempt) => {
            const caseMeta = CASE_LIST.find((c) => c.id === attempt.caseId);
            const completed = attempt.status === "completed";
            return (
              <Card
                key={attempt.id}
                className={styles.attemptCard}
                onClick={() => onSelectAttempt(attempt.id)}
              >
                <div className={styles.attemptMain}>
                  <div className={styles.attemptTitle}>
                    {caseMeta?.title ?? attempt.caseId}
                  </div>
                  <div className={styles.attemptMeta}>
                    {modeLabel(t, attempt.mode)}
                    {" · "}
                    {t("dashboard.attempts.startedAt", {
                      date: new Date(attempt.startedAt).toLocaleString(),
                    })}
                  </div>
                </div>
                <div className={styles.attemptRight}>
                  <Pill tone="score" value={completed ? "Excellent" : "Developing"}>
                    {completed
                      ? t("dashboard.attempts.statusCompleted")
                      : t("dashboard.attempts.statusInProgress")}
                  </Pill>
                  <span className={styles.reviewLink}>
                    {t("dashboard.attempts.review")}
                  </span>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
