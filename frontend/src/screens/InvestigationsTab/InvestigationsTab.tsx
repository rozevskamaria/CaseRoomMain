import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../../components/Button";
import { ChatInput } from "../../components/ChatInput";
import { EmptyState } from "../../components/EmptyState";
import { InfoBanner } from "../../components/InfoBanner";
import { MessageBubble } from "../../components/MessageBubble";
import type { MessageType } from "../../components/MessageBubble";
import { TutorCard } from "../../components/TutorCard";
import type { ChatCallbacks, ChatUi, Session, SessionMessage } from "../types";
import styles from "./InvestigationsTab.module.css";

export interface InvestigationsTabProps {
  session: Session;
  ui: ChatUi;
  callbacks: ChatCallbacks;
  investMsgs: SessionMessage[];
  labCount: number;
}

const interpResultCardStyle = { marginBottom: 10 };

export function InvestigationsTab({
  session,
  ui,
  callbacks,
  investMsgs,
  labCount,
}: InvestigationsTabProps) {
  const { t } = useTranslation();
  const labEnd = useRef<HTMLDivElement>(null);
  const { phase } = session;
  const orderedCount = session.orderedTests.length;

  useEffect(() => {
    labEnd.current?.scrollIntoView();
  }, [investMsgs.length]);

  const showProposeBanner =
    labCount >= 3 && !["differential", "final", "feedback"].includes(phase);
  const showInterpretBanner =
    orderedCount >= 2 && !["interpretation", "final", "feedback"].includes(phase);

  return (
    <div className={styles.tab}>
      <div className={styles.scroll}>
        {investMsgs.length === 0 ? (
          <EmptyState
            icon="🔬"
            title={t("investigations.emptyTitle")}
            description={
              <>
                {t("investigations.emptyDescPre")}
                <strong>{t("investigations.emptyDescOrder")}</strong>
                {t("investigations.emptyDescPost")}
                <br />
                <em>{t("investigations.emptyDescExample")}</em>
              </>
            }
          />
        ) : (
          <div>
            <div className={styles.orderedCount}>
              {t("investigations.orderedCount", { count: orderedCount })}
            </div>
            {investMsgs.map((m) => (
              <MessageBubble
                key={m.id}
                type={m.type as MessageType}
                text={m.text}
              />
            ))}
            <div ref={labEnd} />
          </div>
        )}
      </div>

      {showProposeBanner && (
        <InfoBanner
          tone="teal"
          message={t("investigations.proposeBanner")}
          action={
            <Button
              variant="secondary"
              style={{ borderColor: "var(--teal)", color: "var(--teal)" }}
              onClick={callbacks.proposeDifferentials}
            >
              {t("investigations.proposeDifferentials")}
            </Button>
          }
        />
      )}

      {showInterpretBanner && (
        <InfoBanner
          tone="navy"
          message={t("investigations.interpretBanner")}
          action={
            <Button variant="primary" onClick={callbacks.interpretResults}>
              {t("investigations.interpretResultsAction")}
            </Button>
          }
        />
      )}

      {phase === "interpretation" && ui.inputMode === "interp_input" ? (
        <div className={styles.footer}>
          <div className={styles.footerHint}>{t("investigations.interpretHint")}</div>
          <textarea
            className={styles.interpTextarea}
            value={session.interpText}
            onChange={(e) => callbacks.onSetInterpText(e.target.value)}
            placeholder={t("investigations.interpretPlaceholder")}
          />
          <Button
            variant="primary"
            onClick={callbacks.onSubmitInterpretation}
            disabled={ui.busy || !session.interpText.trim()}
          >
            {t("investigations.submitInterpretation")}
          </Button>
        </div>
      ) : session.interpResult ? (
        <div className={styles.footer}>
          <TutorCard text={session.interpResult} style={interpResultCardStyle} />
          <div className={styles.nextActionsLabel}>
            {t("investigations.nextActionsLabel")}
          </div>
          <div className={styles.nextActionsRow}>
            <Button variant="primary" onClick={callbacks.submitFinal}>
              {t("investigations.submitFinalAnswer")}
            </Button>
            <Button
              variant="secondary"
              onClick={() => callbacks.onSetTab("consultation")}
            >
              {t("investigations.askParentMore")}
            </Button>
            <Button variant="ghost" onClick={callbacks.orderInvestigations}>
              {t("investigations.orderMoreTests")}
            </Button>
          </div>
        </div>
      ) : (
        <div className={styles.orderArea}>
          <div className={styles.orderLabel}>{t("investigations.orderLabel")}</div>
          <ChatInput
            value={ui.input}
            onChange={(e) => callbacks.onSetInput(e.target.value)}
            onSend={callbacks.onOrderTests}
            placeholder={t("investigations.orderPlaceholder")}
            disabled={ui.busy}
            sendLabel={t("investigations.orderSendLabel")}
          />
        </div>
      )}
    </div>
  );
}
