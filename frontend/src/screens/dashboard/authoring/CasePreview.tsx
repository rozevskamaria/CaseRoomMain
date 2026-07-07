import { useQuery } from "@apollo/client";
import { useTranslation } from "react-i18next";
import { Callout } from "../../../components/Callout";
import { LabResultCard } from "../../../components/LabResultCard";
import { formatLabText } from "../../../lib/labText";
import { PreviewCaseQuery } from "../../../graphql/authoringOperations";
import { DashboardSpinner } from "../DashboardShell";
import styles from "./CasePreview.module.css";

export interface CasePreviewProps {
  versionId: string;
  language: string;
}

function asLabData(value: unknown): [string, string][] {
  if (value === null || typeof value !== "object") return [];
  return Object.entries(value as Record<string, unknown>).map(([key, v]) => [
    key,
    typeof v === "string" ? v : String(v),
  ]);
}

function asList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => (typeof item === "string" ? item : String(item)));
}

export function CasePreview({ versionId, language }: CasePreviewProps) {
  const { t } = useTranslation();
  const { data, loading, error } = useQuery(PreviewCaseQuery, {
    variables: { versionId, language },
    fetchPolicy: "cache-and-network",
  });

  if (loading && data === undefined) {
    return <DashboardSpinner />;
  }
  if (error || !data?.previewCase) {
    return <Callout tone="amber">{error?.message ?? t("dashboard.cases.preview.error")}</Callout>;
  }

  const c = data.previewCase;
  const labData = asLabData(c.labData);
  const keyClues = c.keyClues;
  const redFlags = c.redFlags;

  return (
    <div className={styles.preview}>
      <Callout tone="amber">{t("dashboard.cases.preview.banner")}</Callout>

      <section className={styles.block}>
        <h3 className={styles.title}>{c.title}</h3>
        <div className={styles.meta}>
          {c.topic} · {c.difficulty} · {c.targetDiagnosis} · {c.targetIuis}
        </div>
        <div className={styles.patient}>{c.patient}</div>
      </section>

      <section className={styles.block}>
        <div className={styles.label}>{t("dashboard.cases.preview.opening")}</div>
        <div className={styles.prose}>{c.openingClinical}</div>
        <div className={styles.prose}>{c.opening}</div>
      </section>

      <section className={styles.block}>
        <div className={styles.label}>{t("dashboard.cases.preview.parentPrompt")}</div>
        <pre className={styles.code}>{c.parentPrompt}</pre>
      </section>

      <section className={styles.block}>
        <div className={styles.label}>{t("dashboard.cases.preview.examFindings")}</div>
        <div className={styles.prose}>{c.examFindings}</div>
      </section>

      <section className={styles.block}>
        <div className={styles.label}>{t("dashboard.cases.preview.labData")}</div>
        {labData.length === 0 ? (
          <div className={styles.prose}>{t("dashboard.cases.preview.noLabs")}</div>
        ) : (
          <div className={styles.labs}>
            {labData.map(([name, result]) => (
              <LabResultCard key={name} text={formatLabText(name, result)} />
            ))}
          </div>
        )}
      </section>

      <section className={styles.block}>
        <div className={styles.label}>{t("dashboard.cases.preview.modelAnswers")}</div>
        <div className={styles.prose}>{c.modelDiagnosis}</div>
        <div className={styles.prose}>{c.modelManagement}</div>
        <div className={styles.prose}>{c.modelGeneticCounselling}</div>
      </section>

      <section className={styles.block}>
        <div className={styles.label}>{t("dashboard.cases.preview.keyClues")}</div>
        <ul className={styles.list}>
          {asList(keyClues).map((clue, i) => (
            <li key={i}>{clue}</li>
          ))}
        </ul>
      </section>

      <section className={styles.block}>
        <div className={styles.label}>{t("dashboard.cases.preview.redFlags")}</div>
        <ul className={styles.list}>
          {asList(redFlags).map((flag, i) => (
            <li key={i}>{flag}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
