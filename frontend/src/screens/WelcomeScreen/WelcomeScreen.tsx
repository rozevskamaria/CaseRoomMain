import { Button } from "../../components/Button";
import { Callout } from "../../components/Callout";
import { Pill } from "../../components/Pill";
import { CASE_LIST } from "../../content/caseList";
import type { CaseMeta } from "../../content/caseList";
import type { Mode } from "../../state/uiState";
import styles from "./WelcomeScreen.module.css";

export interface WelcomeScreenProps {
  cases?: CaseMeta[];
  mode: Mode;
  seenCases: string[];
  allDone: boolean;
  showBrowse: boolean;
  onSetMode: (mode: Mode) => void;
  onStartRandom: () => void;
  onStartCase: (caseId: string) => void;
  onToggleBrowse: () => void;
  onResetProgress: () => void;
}

const STEPS: [string, string][] = [
  ["1", "A patient is presented to you with a brief clinical description, similar to what you might observe when they first enter your consulting room."],
  ["2", "You take the history by asking questions directly to the parent or patient. They will only provide information in response to the questions you ask, so the more targeted your questions are, the more relevant information you will gather."],
  ["3", "You may request a physical examination at any time by specifying what you would like to examine."],
  ["4", "You can order investigations in the Investigations tab, shown in the panel above. Results will appear as they would in clinical practice. You may interpret the findings and use them to develop a differential diagnosis."],
  ["5", "When you feel ready, submit your final diagnosis and management plan. The simulator will then provide structured formative feedback on your clinical reasoning."],
  ["6", "Each patient you see in a session will be different. The same case will not appear again until you have worked through all available cases."],
];

const MODES: [Mode, string, string][] = [
  ["practice", "With clinical guidance", "The tutor gives gentle prompts when you submit answers. Contextual hints available any time. Recommended for first attempts."],
  ["exam", "Independent — minimal guidance", "Fewer proactive prompts from the tutor. Contextual hints still available if you get stuck. Full structured feedback at the end."],
  ["reflection", "Reflection mode", "After completing a case, the simulator asks five reflective questions about your reasoning. Best used after practice or exam mode."],
];

function difficultyTone(difficulty: string): "adv" | "int" | "beg" {
  if (difficulty === "Advanced") return "adv";
  if (difficulty === "Intermediate") return "int";
  return "beg";
}

export function WelcomeScreen({
  cases = CASE_LIST,
  mode,
  seenCases,
  allDone,
  showBrowse,
  onSetMode,
  onStartRandom,
  onStartCase,
  onToggleBrowse,
  onResetProgress,
}: WelcomeScreenProps) {
  const unseenCount = cases.filter((c) => !seenCases.includes(c.id)).length;
  const completedCount = seenCases.length;

  const ctaLabel =
    unseenCount === cases.length
      ? "See next patient →"
      : `See next patient → (${unseenCount} remaining)`;

  return (
    <div className={styles.root}>
      <div className={styles.welcome}>
        <div className={styles.header}>
          <div className={styles.logo}>Rīga Stradiņš University · Faculty of Medicine</div>
          <h1 className={styles.heroTitle}>Clinical Immunology</h1>
          <div className={styles.heroSub}>Immunology Department — Outpatient Clinic Simulator</div>
          <p className={styles.intro}>
            You are a junior doctor working a session at the Immunology Department outpatient clinic. Patients with suspected inborn errors of immunity have been referred to you. Your task is to take a thorough history, examine the patient, order appropriate investigations, form a differential diagnosis, and propose a management plan.
          </p>
        </div>

        <div className={styles.card}>
          <div className={styles.cardHeading}>How the session works</div>
          {STEPS.map(([n, text]) => (
            <div key={n} className={styles.stepRow}>
              <div className={styles.stepNumber}>{n}</div>
              <div className={styles.stepText}>{text}</div>
            </div>
          ))}
        </div>

        <Callout tone="teal" style={{ marginBottom: 28 }}>
          🌿 <strong>Safe learning environment.</strong> You are encouraged to form hypotheses, make mistakes, change your mind, and learn from the consequences. There are no wrong questions. The goal is to practise clinical reasoning, not to guess the correct answer immediately.
        </Callout>

        <div className={styles.modeBlock}>
          <div className={styles.cardHeading}>Choose your session mode</div>
          {MODES.map(([m, label, desc]) => (
            <div
              key={m}
              className={`${styles.modeCard}${mode === m ? ` ${styles.modeCardActive}` : ""}`}
              onClick={() => onSetMode(m)}
            >
              <div className={styles.modeCardInner}>
                <div className={`${styles.modeRadio}${mode === m ? ` ${styles.modeRadioActive}` : ""}`} />
                <div>
                  <div className={styles.modeLabel}>{label}</div>
                  <div className={styles.modeDesc}>{desc}</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {completedCount > 0 && (
          <div className={styles.progress}>
            <div>
              <span className={styles.progressLabel}>Session progress: </span>
              <span className={styles.progressCount}>
                {completedCount} of {cases.length} cases seen
              </span>
              <div className={styles.pips}>
                {cases.map((c) => (
                  <div
                    key={c.id}
                    className={`${styles.pip}${seenCases.includes(c.id) ? ` ${styles.pipSeen}` : ""}`}
                    title={c.title}
                  />
                ))}
              </div>
            </div>
            <Button variant="ghost" style={{ fontSize: "12px" }} onClick={onResetProgress}>
              Reset
            </Button>
          </div>
        )}

        {allDone && (
          <Callout tone="amber" style={{ padding: "14px 18px", marginBottom: 20 }}>
            🎉 <strong>You have seen all {cases.length} available cases.</strong> Reset your progress to start again, or browse individual cases below.
          </Callout>
        )}

        <button
          className={`${styles.cta}${allDone ? ` ${styles.ctaDone}` : ""}`}
          onClick={onStartRandom}
          disabled={allDone}
        >
          {allDone ? "All cases completed" : ctaLabel}
        </button>

        <div className={styles.browseToggleWrap}>
          <Button variant="ghost" style={{ fontSize: "13px" }} onClick={onToggleBrowse}>
            {showBrowse ? "Hide case list ↑" : "Browse cases individually ↓"}
          </Button>
        </div>

        {showBrowse && (
          <div className={styles.browseList}>
            <div className={styles.browseNote}>
              Note: selecting a specific case manually will not mark it as seen in your progress.
            </div>
            {cases.map((c) => (
              <div
                key={c.id}
                className={`${styles.caseCard}${seenCases.includes(c.id) ? ` ${styles.caseCardSeen}` : ""}`}
                onClick={() => onStartCase(c.id)}
              >
                <div className={styles.caseCardTop}>
                  <div>
                    <div className={styles.caseTitle}>{c.title}</div>
                    <div className={styles.caseMeta}>
                      {c.patient} · {c.topic}
                    </div>
                  </div>
                  <div className={styles.caseTags}>
                    {seenCases.includes(c.id) && <span className={styles.seenBadge}>✓ seen</span>}
                    <Pill tone="difficulty" value={difficultyTone(c.difficulty)}>
                      {c.difficulty}
                    </Pill>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
