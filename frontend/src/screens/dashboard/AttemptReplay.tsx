import { useState } from "react";
import { useQuery } from "@apollo/client";
import { useTranslation } from "react-i18next";
import { FeedbackReport } from "../../components/FeedbackReport";
import type { Feedback } from "../../components/FeedbackReport";
import type { DiagnosticAccuracy } from "../../components/AccuracyBanner";
import { MessageBubble } from "../../components/MessageBubble";
import type { MessageType } from "../../components/MessageBubble";
import { TabBar } from "../../components/TabBar";
import { CASE_LIST } from "../../content/caseList";
import { SessionQuery } from "../../graphql/operations";
import type { SessionFieldsFragment } from "../../gql/graphql";
import { projectReplay } from "../../lib/replayProjection";
import { DashboardSpinner } from "./DashboardShell";
import styles from "./AttemptReplay.module.css";

export interface AttemptReplayProps {
  attemptId: string;
}

type ReplayTab = "consultation" | "investigations" | "feedback";

function toFeedback(session: SessionFieldsFragment): Feedback | null {
  const fb = session.feedback;
  if (!fb) return null;
  return {
    diagnosticAccuracy: fb.diagnosticAccuracy as DiagnosticAccuracy,
    diagnosticComment: fb.diagnosticComment,
    wellDone: fb.wellDone,
    missing: fb.missing,
    keyClues: fb.keyClues,
    reasoningPathway: fb.reasoningPathway,
    managementPoints: fb.managementPoints,
    geneticPoints: fb.geneticPoints,
    revisionTopic: fb.revisionTopic,
    scores: fb.scores
      ? {
          historyTaking: fb.scores.historyTaking,
          examination: fb.scores.examination,
          differential: fb.scores.differential,
          testSelection: fb.scores.testSelection,
          interpretation: fb.scores.interpretation,
          management: fb.scores.management,
        }
      : {},
  };
}

export function AttemptReplay({ attemptId }: AttemptReplayProps) {
  const { t } = useTranslation();
  const [tab, setTab] = useState<ReplayTab>("consultation");
  const { data, loading } = useQuery(SessionQuery, {
    variables: { id: attemptId },
    fetchPolicy: "cache-and-network",
  });

  if (loading && data === undefined) {
    return <DashboardSpinner />;
  }

  const session = data?.session ?? null;
  if (session === null) {
    return <div className={styles.notFound}>{t("dashboard.replay.notFound")}</div>;
  }

  const { consultation, investigations, labCount } = projectReplay(session);
  const feedback = toFeedback(session);
  const caseMeta = CASE_LIST.find((c) => c.id === session.caseId);
  const caseTitle = caseMeta?.title ?? session.caseId;

  return (
    <div className={styles.view}>
      <h2 className={styles.heading}>{t("dashboard.replay.heading")}</h2>
      <div className={styles.caseTitle}>{caseTitle}</div>
      <div className={styles.readOnlyBanner}>
        {t("dashboard.replay.readOnlyBanner")}
      </div>

      <TabBar
        tabs={[
          { key: "consultation", label: t("dashboard.replay.tabConsultation") },
          {
            key: "investigations",
            label: t("dashboard.replay.tabInvestigations"),
            badge: labCount,
          },
          { key: "feedback", label: t("dashboard.replay.tabFeedback") },
        ]}
        active={tab}
        onChange={(key) => setTab(key as ReplayTab)}
      />

      <div className={styles.panel}>
        {tab === "consultation" &&
          (consultation.length === 0 ? (
            <div className={styles.empty}>{t("dashboard.replay.noConsultation")}</div>
          ) : (
            consultation.map((m) => (
              <MessageBubble key={m.id} type={m.type as MessageType} text={m.text} />
            ))
          ))}

        {tab === "investigations" &&
          (investigations.length === 0 ? (
            <div className={styles.empty}>
              {t("dashboard.replay.noInvestigations")}
            </div>
          ) : (
            investigations.map((m) => (
              <MessageBubble key={m.id} type={m.type as MessageType} text={m.text} />
            ))
          ))}

        {tab === "feedback" &&
          (feedback ? (
            <FeedbackReport
              feedback={feedback}
              caseTitle={caseTitle}
              mode={session.mode}
              showActions={false}
            />
          ) : (
            <div className={styles.empty}>{t("dashboard.replay.noFeedback")}</div>
          ))}
      </div>
    </div>
  );
}
