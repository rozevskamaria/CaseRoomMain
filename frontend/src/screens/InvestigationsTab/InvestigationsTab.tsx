import { useEffect, useRef } from "react";
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
            title="No investigations ordered yet"
            description={
              <>
                Type test names in the field below and press{" "}
                <strong>Order</strong> — for example:
                <br />
                <em>"CBC, CRP, immunoglobulins, chest X-ray"</em>
              </>
            }
          />
        ) : (
          <div>
            <div className={styles.orderedCount}>
              {orderedCount} investigation{orderedCount !== 1 ? "s" : ""} ordered
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
          message="You have enough results to form a differential."
          action={
            <Button
              variant="secondary"
              style={{ borderColor: "var(--teal)", color: "var(--teal)" }}
              onClick={callbacks.proposeDifferentials}
            >
              📋 Propose differentials
            </Button>
          }
        />
      )}

      {showInterpretBanner && (
        <InfoBanner
          tone="navy"
          message="Ready to interpret your results?"
          action={
            <Button variant="primary" onClick={callbacks.interpretResults}>
              → Interpret results
            </Button>
          }
        />
      )}

      {phase === "interpretation" && ui.inputMode === "interp_input" ? (
        <div className={styles.footer}>
          <div className={styles.footerHint}>
            Interpret your findings — write your reasoning below
          </div>
          <textarea
            className={styles.interpTextarea}
            value={session.interpText}
            onChange={(e) => callbacks.onSetInterpText(e.target.value)}
            placeholder="Which results are most significant? What do they tell you about the likely diagnosis?"
          />
          <Button
            variant="primary"
            onClick={callbacks.onSubmitInterpretation}
            disabled={ui.busy || !session.interpText.trim()}
          >
            Submit interpretation
          </Button>
        </div>
      ) : session.interpResult ? (
        <div className={styles.footer}>
          <TutorCard text={session.interpResult} style={interpResultCardStyle} />
          <div className={styles.nextActionsLabel}>
            What would you like to do next?
          </div>
          <div className={styles.nextActionsRow}>
            <Button variant="primary" onClick={callbacks.submitFinal}>
              → Submit final answer
            </Button>
            <Button
              variant="secondary"
              onClick={() => callbacks.onSetTab("consultation")}
            >
              ← Ask the parent more questions
            </Button>
            <Button variant="ghost" onClick={callbacks.orderInvestigations}>
              Order more tests
            </Button>
          </div>
        </div>
      ) : (
        <div className={styles.orderArea}>
          <div className={styles.orderLabel}>
            Order a test — type name(s) and press Enter or Order
          </div>
          <ChatInput
            value={ui.input}
            onChange={(e) => callbacks.onSetInput(e.target.value)}
            onSend={callbacks.onOrderTests}
            placeholder={'e.g. "CBC, CRP, immunoglobulins, chest X-ray, flow cytometry"'}
            disabled={ui.busy}
            sendLabel="Order"
          />
        </div>
      )}
    </div>
  );
}
