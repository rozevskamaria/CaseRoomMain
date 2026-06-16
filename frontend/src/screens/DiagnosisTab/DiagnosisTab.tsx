import type { CSSProperties } from "react";
import { Button } from "../../components/Button";
import { EmptyState } from "../../components/EmptyState";
import { LabeledTextarea } from "../../components/LabeledTextarea";
import type {
  ChatCallbacks,
  ChatUi,
  FinalAnswerField,
  Session,
} from "../types";
import styles from "./DiagnosisTab.module.css";

export interface DiagnosisTabProps {
  session: Session;
  ui: ChatUi;
  callbacks: ChatCallbacks;
}

const FINAL_FIELDS: [FinalAnswerField, string][] = [
  ["diagnosis", "Most likely diagnosis"],
  ["findings", "Main supporting findings (3–5 bullet points)"],
  ["differentials", "Differential diagnoses"],
  ["tests", "Additional tests or confirmatory testing"],
  ["management", "Initial management plan"],
  ["genetics", "Genetic counselling and family implications"],
  ["explanation", "How would you explain this to the parent?"],
];

const emptyStyle: CSSProperties = {
  ["--empty-max-width" as string]: "480px",
  ["--empty-margin" as string]: "52px auto 0",
  ["--empty-title-size" as string]: "18px",
};

const submitGateStyle: CSSProperties = { padding: "12px 32px", fontSize: 15 };
const submitFormStyle: CSSProperties = { marginTop: 10, padding: "10px 28px" };

export function DiagnosisTab({ session, ui, callbacks }: DiagnosisTabProps) {
  const orderedCount = session.orderedTests.length;
  const canSubmit = orderedCount >= 1 || session.examDone;

  return (
    <div className={styles.tab}>
      {!ui.showFinalForm ? (
        <EmptyState
          style={emptyStyle}
          icon="📋"
          title="Final Diagnosis"
          description="Complete your consultation, examine the patient, and order investigations before submitting your final diagnosis. When you are ready, click below."
          action={
            canSubmit ? (
              <Button
                variant="primary"
                style={submitGateStyle}
                onClick={callbacks.submitFinal}
              >
                → Submit final diagnosis
              </Button>
            ) : (
              <div className={styles.warning}>
                Please take a history and order at least one investigation before
                submitting a diagnosis.
              </div>
            )
          }
        />
      ) : (
        <div>
          <div className={styles.formTitle}>Submit your final answer</div>
          {FINAL_FIELDS.map(([key, label]) => (
            <LabeledTextarea
              key={key}
              label={label}
              value={session.finalAnswer[key]}
              onChange={(e) => callbacks.onSetFinalAnswerField(key, e.target.value)}
              rows={key === "explanation" ? 3 : 2}
            />
          ))}
          <Button
            variant="primary"
            style={submitFormStyle}
            onClick={callbacks.onSubmitFinalAnswer}
            disabled={ui.busy || !session.finalAnswer.diagnosis.trim()}
          >
            {ui.busy ? "Generating feedback…" : "Submit final answer"}
          </Button>
        </div>
      )}
    </div>
  );
}
