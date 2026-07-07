import { useState } from "react";
import { useMutation, useQuery } from "@apollo/client";
import { useTranslation } from "react-i18next";
import { Button } from "../../../components/Button";
import { Card } from "../../../components/Card";
import { EmptyState } from "../../../components/EmptyState";
import { Pill } from "../../../components/Pill";
import { TextInput } from "../../../components/TextInput";
import { Callout } from "../../../components/Callout";
import {
  AuthorCasesQuery,
  CreateCaseDraftMutation,
} from "../../../graphql/authoringOperations";
import { DashboardSpinner } from "../DashboardShell";
import styles from "./CasesView.module.css";

export interface CasesViewProps {
  onOpenDraft: (versionId: string) => void;
}

interface CaseSummary {
  caseId: string;
  slug: string;
  versionId: string;
  versionNo: number;
  status: string;
  isCurrent: boolean;
  difficulty: string;
  topic: string;
  targetDiagnosis: string;
  iuis: string;
  hasLv: boolean;
}

export function CasesView({ onOpenDraft }: CasesViewProps) {
  const { t } = useTranslation();
  const { data, loading } = useQuery(AuthorCasesQuery, {
    fetchPolicy: "cache-and-network",
  });
  const [createDraft, { loading: creating }] = useMutation(CreateCaseDraftMutation, {
    refetchQueries: [{ query: AuthorCasesQuery }],
  });
  const [showCreate, setShowCreate] = useState(false);
  const [slug, setSlug] = useState("");
  const [error, setError] = useState<string | null>(null);

  const cases = (data?.authorCases ?? []) as CaseSummary[];
  const drafts = cases.filter((c) => c.status === "draft");
  const published = cases.filter((c) => c.status === "published");

  const onCreateNew = () => {
    const value = slug.trim();
    if (!value || creating) return;
    setError(null);
    void createDraft({ variables: { slug: value, fromVersionId: null } })
      .then((res) => {
        const created = res.data?.createCaseDraft;
        setSlug("");
        setShowCreate(false);
        if (created) onOpenDraft(created.versionId);
      })
      .catch((err: Error) => setError(err.message));
  };

  const onEditPublished = (versionId: string) => {
    if (creating) return;
    setError(null);
    void createDraft({ variables: { slug: null, fromVersionId: versionId } })
      .then((res) => {
        const created = res.data?.createCaseDraft;
        if (created) onOpenDraft(created.versionId);
      })
      .catch((err: Error) => setError(err.message));
  };

  if (loading && data === undefined) {
    return <DashboardSpinner />;
  }

  return (
    <div className={styles.view}>
      <div className={styles.headRow}>
        <div>
          <h2 className={styles.heading}>{t("dashboard.cases.heading")}</h2>
          <p className={styles.intro}>{t("dashboard.cases.intro")}</p>
        </div>
        <Button variant="secondary" onClick={() => setShowCreate((v) => !v)}>
          {t("dashboard.cases.newCase")}
        </Button>
      </div>

      {error && <Callout tone="amber">{error}</Callout>}

      {showCreate && (
        <Card className={styles.createCard}>
          <div className={styles.createHeading}>
            {t("dashboard.cases.createHeading")}
          </div>
          <div className={styles.formBlock}>
            <TextInput
              id="case-slug"
              label={t("dashboard.cases.slugLabel")}
              value={slug}
              onChange={setSlug}
              placeholder={t("dashboard.cases.slugPlaceholder")}
            />
            <Button
              variant="primary"
              disabled={!slug.trim() || creating}
              onClick={onCreateNew}
            >
              {t("dashboard.cases.createSubmit")}
            </Button>
          </div>
        </Card>
      )}

      <section className={styles.group}>
        <h3 className={styles.groupHeading}>{t("dashboard.cases.draftsHeading")}</h3>
        {drafts.length === 0 ? (
          <EmptyState
            icon="✏️"
            title={t("dashboard.cases.draftsEmptyTitle")}
            description={t("dashboard.cases.draftsEmptyDescription")}
          />
        ) : (
          <div className={styles.list}>
            {drafts.map((c) => (
              <Card
                key={c.versionId}
                className={styles.caseCard}
                onClick={() => onOpenDraft(c.versionId)}
              >
                <div className={styles.caseMain}>
                  <div className={styles.caseSlug}>{c.slug}</div>
                  <div className={styles.caseMeta}>
                    {c.targetDiagnosis || t("dashboard.cases.untitled")}
                  </div>
                </div>
                <div className={styles.pills}>
                  <Pill tone="count">
                    {t("dashboard.cases.versionLabel", { no: c.versionNo })}
                  </Pill>
                  <Pill tone="count">{t("dashboard.cases.statusDraft")}</Pill>
                  <Pill tone="count">
                    {c.hasLv
                      ? t("dashboard.cases.lvComplete")
                      : t("dashboard.cases.lvMissing")}
                  </Pill>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className={styles.group}>
        <h3 className={styles.groupHeading}>
          {t("dashboard.cases.publishedHeading")}
        </h3>
        {published.length === 0 ? (
          <EmptyState
            icon="📚"
            title={t("dashboard.cases.publishedEmptyTitle")}
            description={t("dashboard.cases.publishedEmptyDescription")}
          />
        ) : (
          <div className={styles.list}>
            {published.map((c) => (
              <Card key={c.versionId} className={styles.caseCard}>
                <div className={styles.caseMain}>
                  <div className={styles.caseSlug}>{c.slug}</div>
                  <div className={styles.caseMeta}>
                    {c.targetDiagnosis || t("dashboard.cases.untitled")}
                  </div>
                </div>
                <div className={styles.pills}>
                  <Pill tone="count">
                    {t("dashboard.cases.versionLabel", { no: c.versionNo })}
                  </Pill>
                  <Pill tone="count">{t("dashboard.cases.statusPublished")}</Pill>
                  <Pill tone="count">
                    {c.hasLv
                      ? t("dashboard.cases.lvComplete")
                      : t("dashboard.cases.lvMissing")}
                  </Pill>
                  <Button
                    variant="ghost"
                    disabled={creating}
                    onClick={() => onEditPublished(c.versionId)}
                  >
                    {t("dashboard.cases.edit")}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
