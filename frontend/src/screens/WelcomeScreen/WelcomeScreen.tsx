import { useTranslation } from "react-i18next";
import { Button } from "../../components/Button";
import { Callout } from "../../components/Callout";
import { LocaleSwitcher } from "../../components/LocaleSwitcher";
import { Pill } from "../../components/Pill";
import { CASE_LIST } from "../../content/caseList";
import type { CaseMeta } from "../../content/caseList";
import type { Locale } from "../../i18n/types";
import type { Mode } from "../../state/uiState";
import styles from "./WelcomeScreen.module.css";

export interface WelcomeScreenProps {
  cases?: CaseMeta[];
  mode: Mode;
  language: Locale;
  seenCases: string[];
  allDone: boolean;
  showBrowse: boolean;
  onSetMode: (mode: Mode) => void;
  onSetLanguage: (language: Locale) => void;
  onStartRandom: () => void;
  onStartCase: (caseId: string) => void;
  onToggleBrowse: () => void;
  onResetProgress: () => void;
  onLogout?: () => void;
}

const STEP_IDS = ["1", "2", "3", "4", "5", "6"] as const;

const MODE_IDS: Mode[] = ["practice", "exam", "reflection"];

function difficultyTone(difficulty: string): "adv" | "int" | "beg" {
  if (difficulty === "Advanced") return "adv";
  if (difficulty === "Intermediate") return "int";
  return "beg";
}

export function WelcomeScreen({
  cases = CASE_LIST,
  mode,
  language,
  seenCases,
  allDone,
  showBrowse,
  onSetMode,
  onSetLanguage,
  onStartRandom,
  onStartCase,
  onToggleBrowse,
  onResetProgress,
  onLogout,
}: WelcomeScreenProps) {
  const { t } = useTranslation();
  const unseenCount = cases.filter((c) => !seenCases.includes(c.id)).length;
  const completedCount = seenCases.length;

  const ctaLabel =
    unseenCount === cases.length
      ? t("welcome.ctaBase")
      : t("welcome.ctaRemaining", { count: unseenCount });

  return (
    <div className={styles.root}>
      <div className={styles.welcome}>
        <div className={styles.header}>
          <div className={styles.topBar}>
            <LocaleSwitcher value={language} onChange={onSetLanguage} />
            {onLogout && (
              <Button variant="ghost" style={{ fontSize: "12px" }} onClick={onLogout}>
                {t("welcome.signOut")}
              </Button>
            )}
          </div>
          <div className={styles.logo}>{t("welcome.logoLine")}</div>
          <h1 className={styles.heroTitle}>{t("welcome.heroTitle")}</h1>
          <div className={styles.heroSub}>{t("welcome.heroSub")}</div>
          <p className={styles.intro}>{t("welcome.intro")}</p>
        </div>

        <div className={styles.card}>
          <div className={styles.cardHeading}>{t("welcome.howItWorksHeading")}</div>
          {STEP_IDS.map((n) => (
            <div key={n} className={styles.stepRow}>
              <div className={styles.stepNumber}>{n}</div>
              <div className={styles.stepText}>{t(`welcome.steps.${n}`)}</div>
            </div>
          ))}
        </div>

        <Callout tone="teal" style={{ marginBottom: 28 }}>
          {t("welcome.safetyEmoji")}
          <strong>{t("welcome.safetyStrong")}</strong>
          {t("welcome.safetyBody")}
        </Callout>

        <div className={styles.modeBlock}>
          <div className={styles.cardHeading}>{t("welcome.modeHeading")}</div>
          {MODE_IDS.map((m) => (
            <div
              key={m}
              className={`${styles.modeCard}${mode === m ? ` ${styles.modeCardActive}` : ""}`}
              onClick={() => onSetMode(m)}
            >
              <div className={styles.modeCardInner}>
                <div className={`${styles.modeRadio}${mode === m ? ` ${styles.modeRadioActive}` : ""}`} />
                <div>
                  <div className={styles.modeLabel}>{t(`welcome.modes.${m}Label`)}</div>
                  <div className={styles.modeDesc}>{t(`welcome.modes.${m}Desc`)}</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {completedCount > 0 && (
          <div className={styles.progress}>
            <div>
              <span className={styles.progressLabel}>{t("welcome.progressLabel")}</span>
              <span className={styles.progressCount}>
                {t("welcome.progressCount", {
                  completed: completedCount,
                  total: cases.length,
                })}
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
              {t("welcome.reset")}
            </Button>
          </div>
        )}

        {allDone && (
          <Callout tone="amber" style={{ padding: "14px 18px", marginBottom: 20 }}>
            {t("welcome.allDoneEmoji")}
            <strong>{t("welcome.allDoneStrong", { total: cases.length })}</strong>
            {t("welcome.allDoneBody")}
          </Callout>
        )}

        <button
          className={`${styles.cta}${allDone ? ` ${styles.ctaDone}` : ""}`}
          onClick={onStartRandom}
          disabled={allDone}
        >
          {allDone ? t("welcome.ctaAllDone") : ctaLabel}
        </button>

        <div className={styles.browseToggleWrap}>
          <Button variant="ghost" style={{ fontSize: "13px" }} onClick={onToggleBrowse}>
            {showBrowse ? t("welcome.browseHide") : t("welcome.browseShow")}
          </Button>
        </div>

        {showBrowse && (
          <div className={styles.browseList}>
            <div className={styles.browseNote}>{t("welcome.browseNote")}</div>
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
                    {seenCases.includes(c.id) && (
                      <span className={styles.seenBadge}>{t("welcome.seenBadge")}</span>
                    )}
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
