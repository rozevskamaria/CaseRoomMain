import { useEffect, useRef } from "react";
import { Button } from "../../components/Button";
import { ChatInput } from "../../components/ChatInput";
import { FeedbackReport } from "../../components/FeedbackReport";
import type { Feedback } from "../../components/FeedbackReport";
import type { DiagnosticAccuracy } from "../../components/AccuracyBanner";
import { MessageBubble } from "../../components/MessageBubble";
import type { MessageType } from "../../components/MessageBubble";
import { TypingIndicator } from "../../components/TypingIndicator";
import { REFLECTION_QS } from "../../state/phases";
import type {
  CaseMeta,
  ChatCallbacks,
  ChatUi,
  Session,
  SessionMessage,
} from "../types";
import styles from "./ConsultationTab.module.css";

export interface ConsultationTabProps {
  session: Session;
  caseMeta: CaseMeta;
  ui: ChatUi;
  callbacks: ChatCallbacks;
  chatMsgs: SessionMessage[];
}

const ACTION_PHASES = [
  "history",
  "summary",
  "examination",
  "differential",
  "tests",
  "interpretation",
];

function toFeedback(session: Session): Feedback | null {
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

export function ConsultationTab({
  session,
  caseMeta,
  ui,
  callbacks,
  chatMsgs,
}: ConsultationTabProps) {
  const chatEnd = useRef<HTMLDivElement>(null);
  const { phase } = session;
  const parentCount = session.messages.filter((m) => m.type === "parent").length;
  const orderedCount = session.orderedTests.length;
  const feedback = toFeedback(session);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [session.messages, ui.busy]);

  return (
    <div className={styles.tab}>
      <div className={styles.msgs}>
        {chatMsgs.map((m) => (
          <MessageBubble key={m.id} type={m.type as MessageType} text={m.text} />
        ))}

        {ui.busy && phase !== "feedback" && (
          <TypingIndicator label="Parent" text="Typing…" />
        )}

        {ui.busy && phase === "feedback" && (
          <TypingIndicator text="Generating feedback report…" />
        )}

        {phase === "feedback" && feedback && (
          <FeedbackReport
            feedback={feedback}
            caseTitle={caseMeta.title}
            mode={ui.mode}
            onSeeNext={callbacks.onSeeNext}
            onReflect={callbacks.onReflect}
            onBrowse={callbacks.onBrowse}
          />
        )}

        <div ref={chatEnd} />
      </div>

      {ACTION_PHASES.includes(phase) && (
        <div className={styles.actionBar}>
          <span className={styles.nextStep}>Next step:</span>

          {!session.examDone && parentCount >= 2 && (
            <Button variant="secondary" onClick={callbacks.onRequestExam}>
              🩺 Examine patient
            </Button>
          )}

          {parentCount >= 3 && phase === "history" && (
            <Button variant="ghost" onClick={callbacks.goToSummary}>
              📝 Submit summary
            </Button>
          )}

          {parentCount >= 2 && (
            <Button
              variant="secondary"
              className={styles.orderInvest}
              onClick={() => callbacks.onSetTab("investigations")}
            >
              🔬 Order investigations →
            </Button>
          )}

          {orderedCount >= 2 && phase === "tests" && (
            <Button variant="secondary" onClick={callbacks.interpretResults}>
              📊 Interpret results →
            </Button>
          )}
        </div>
      )}

      {phase === "reflection" && (
        <div className={styles.reflection}>
          <div className={styles.reflectionMeta}>
            Reflection question {session.reflectionStep + 1} of {REFLECTION_QS.length}:
          </div>
          <div className={styles.reflectionQuestion}>
            {REFLECTION_QS[session.reflectionStep]}
          </div>
          <div className={styles.reflectionRow}>
            <input
              className={styles.reflectionInput}
              value={ui.input}
              onChange={(e) => callbacks.onSetInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && callbacks.onSubmitReflection()}
              placeholder="Your reflection..."
            />
            <Button variant="primary" onClick={callbacks.onSubmitReflection}>
              →
            </Button>
          </div>
        </div>
      )}

      {ui.inputMode === "summary_input" && phase === "summary" && (
        <div className={styles.formInput}>
          <textarea
            className={`${styles.reflectionInput} ${styles.formTextarea}`}
            value={session.summary}
            onChange={(e) => callbacks.onSetSummary(e.target.value)}
            placeholder="Write your clinical summary in 2–4 sentences..."
          />
          <Button
            variant="primary"
            onClick={callbacks.onSubmitSummary}
            disabled={ui.busy || !session.summary.trim()}
          >
            Submit summary
          </Button>
        </div>
      )}

      {ui.inputMode === "diff_input" && phase === "differential" && (
        <div className={styles.formInput}>
          <textarea
            className={`${styles.reflectionInput} ${styles.formTextarea}`}
            value={session.differentials}
            onChange={(e) => callbacks.onSetDifferentials(e.target.value)}
            placeholder="State your top 2–3 differential diagnoses..."
          />
          <Button
            variant="primary"
            onClick={callbacks.onSubmitDifferentials}
            disabled={ui.busy || !session.differentials.trim()}
          >
            Submit differentials
          </Button>
        </div>
      )}

      {!["summary_input", "diff_input", "interp_input"].includes(ui.inputMode) &&
        phase !== "reflection" &&
        phase !== "final" && (
          <div className={styles.inputArea}>
            <ChatInput
              value={ui.input}
              onChange={(e) => callbacks.onSetInput(e.target.value)}
              onSend={callbacks.onSend}
              placeholder="Ask the parent a question…"
              disabled={ui.busy}
            />
          </div>
        )}
    </div>
  );
}
