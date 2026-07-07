import type { CSSProperties } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../../components/Button";
import { ChatHeader } from "../../components/ChatHeader";
import { HintDropdown } from "../../components/HintDropdown";
import { HintModal } from "../../components/HintModal";
import { PhaseStepper } from "../../components/PhaseStepper";
import { Pill } from "../../components/Pill";
import { TabBar } from "../../components/TabBar";
import { PHASE_STEPS } from "../../state/phases";
import { ConsultationTab } from "../ConsultationTab";
import { DiagnosisTab } from "../DiagnosisTab";
import { InvestigationsTab } from "../InvestigationsTab";
import type { CaseMeta, ChatCallbacks, ChatUi, Session } from "../types";
import styles from "./ChatScreen.module.css";

export interface ChatScreenProps {
  session: Session;
  caseMeta: CaseMeta;
  ui: ChatUi;
  callbacks: ChatCallbacks;
}

export function ChatScreen({ session, caseMeta, ui, callbacks }: ChatScreenProps) {
  const { t } = useTranslation();
  const modeLabel = (mode: string): string => {
    if (mode === "practice") return t("chat.modePractice");
    if (mode === "exam") return t("chat.modeExam");
    return t("chat.modeReflection");
  };
  const { phase } = session;
  const labMsgs = session.messages.filter((m) => m.type === "lab");
  const investMsgs = session.messages.filter(
    (m) => m.type === "lab" || m.type === "lab_note" || m.type === "lab_tutor",
  );
  const chatMsgs = session.messages.filter(
    (m) => m.type !== "lab" && m.type !== "lab_note" && m.type !== "lab_tutor",
  );

  const hintButtonStyle: CSSProperties = { opacity: ui.busy ? 0.5 : 1 };

  const rightSlot = (
    <>
      {phase !== "feedback" && phase !== "reflection" && (
        <div className={styles.hintAnchor}>
          <Button
            variant="secondary"
            style={hintButtonStyle}
            onClick={() => callbacks.onShowHintMenu(!ui.showHintMenu)}
            disabled={ui.busy}
          >
            {session.hintsUsed > 0
              ? t("chat.needHintUsed", { count: session.hintsUsed })
              : t("chat.needHint")}
          </Button>
          <HintDropdown
            open={ui.showHintMenu}
            hintsUsed={session.hintsUsed}
            onGetHint={callbacks.onGetHint}
          />
        </div>
      )}
      <Pill tone="count">
        {session.language === "lv" ? t("locale.lv") : t("locale.en")}
      </Pill>
      <Button variant="ghost" onClick={callbacks.onExit}>
        {t("chat.exitToClinic")}
      </Button>
    </>
  );

  return (
    <div className={styles.chatWrap}>
      <ChatHeader
        title={caseMeta.title}
        subtitle={`${caseMeta.patient} · ${caseMeta.topic} · ${modeLabel(ui.mode)}`}
        rightSlot={rightSlot}
      />

      <PhaseStepper phases={PHASE_STEPS} currentPhase={phase} />

      <TabBar
        tabs={[
          { key: "consultation", label: t("chat.tabConsultation") },
          { key: "investigations", label: t("chat.tabInvestigations"), badge: labMsgs.length },
          { key: "diagnosis", label: t("chat.tabDiagnosis") },
        ]}
        active={ui.activeTab}
        onChange={(key) => callbacks.onSetTab(key as ChatUi["activeTab"])}
      />

      <div className={styles.tabContent}>
        {ui.activeTab === "consultation" && (
          <ConsultationTab
            session={session}
            caseMeta={caseMeta}
            ui={ui}
            callbacks={callbacks}
            chatMsgs={chatMsgs}
          />
        )}

        {ui.activeTab === "investigations" && (
          <InvestigationsTab
            session={session}
            ui={ui}
            callbacks={callbacks}
            investMsgs={investMsgs}
            labCount={labMsgs.length}
          />
        )}

        {ui.activeTab === "diagnosis" && (
          <DiagnosisTab session={session} ui={ui} callbacks={callbacks} />
        )}
      </div>

      <HintModal
        open={ui.hintPopup !== null}
        text={ui.hintPopup ?? ""}
        onClose={callbacks.onCloseHintPopup}
      />
    </div>
  );
}
