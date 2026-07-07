import type { CSSProperties } from "react";
import { useTranslation } from "react-i18next";
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

const FINAL_FIELDS: FinalAnswerField[] = [
  "diagnosis",
  "findings",
  "differentials",
  "tests",
  "management",
  "genetics",
  "explanation",
];

const emptyStyle: CSSProperties = {
  ["--empty-max-width" as string]: "480px",
  ["--empty-margin" as string]: "52px auto 0",
  ["--empty-title-size" as string]: "18px",
};

const submitGateStyle: CSSProperties = { padding: "12px 32px", fontSize: 15 };
const submitFormStyle: CSSProperties = { marginTop: 10, padding: "10px 28px" };

export function DiagnosisTab({ session, ui, callbacks }: DiagnosisTabProps) {
  const { t } = useTranslation();
  const orderedCount = session.orderedTests.length;
  const canSubmit = orderedCount >= 1 || session.examDone;

  return (
    <div className={styles.tab}>
      {!ui.showFinalForm ? (
        <EmptyState
          style={emptyStyle}
          icon="📋"
          title={t("diagnosis.emptyTitle")}
          description={t("diagnosis.emptyDescription")}
          action={
            canSubmit ? (
              <Button
                variant="primary"
                style={submitGateStyle}
                onClick={callbacks.submitFinal}
              >
                {t("diagnosis.submitGate")}
              </Button>
            ) : (
              <div className={styles.warning}>{t("diagnosis.warning")}</div>
            )
          }
        />
      ) : (
        <div>
          <div className={styles.formTitle}>{t("diagnosis.formTitle")}</div>
          {FINAL_FIELDS.map((key) => (
            <LabeledTextarea
              key={key}
              label={t(`diagnosis.fields.${key}`)}
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
            {ui.busy ? t("diagnosis.generatingFeedback") : t("diagnosis.submitFinalAnswer")}
          </Button>
        </div>
      )}
    </div>
  );
}
