import { useState } from "react";
import { useMutation, useQuery } from "@apollo/client";
import { useTranslation } from "react-i18next";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { Pill } from "../../components/Pill";
import { TextInput } from "../../components/TextInput";
import {
  CreateCohortMutation,
  MyCohortsQuery,
} from "../../graphql/cohortOperations";
import { DashboardSpinner } from "./DashboardShell";
import styles from "./CohortsView.module.css";

export interface CohortsViewProps {
  onSelectCohort: (cohortId: string) => void;
}

export function CohortsView({ onSelectCohort }: CohortsViewProps) {
  const { t } = useTranslation();
  const { data, loading } = useQuery(MyCohortsQuery, {
    fetchPolicy: "cache-and-network",
  });
  const [createCohort, { loading: creating }] = useMutation(CreateCohortMutation, {
    refetchQueries: [{ query: MyCohortsQuery }],
  });
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [academicYear, setAcademicYear] = useState("");

  const cohorts = data?.myCohorts ?? [];

  const onCreate = () => {
    if (!name.trim() || creating) return;
    void createCohort({
      variables: {
        input: { name: name.trim(), academicYear: academicYear.trim() || null },
      },
    }).then(() => {
      setName("");
      setAcademicYear("");
      setShowCreate(false);
    });
  };

  if (loading && data === undefined) {
    return <DashboardSpinner />;
  }

  return (
    <div className={styles.view}>
      <div className={styles.headRow}>
        <div>
          <h2 className={styles.heading}>{t("dashboard.cohorts.heading")}</h2>
          <p className={styles.intro}>{t("dashboard.cohorts.intro")}</p>
        </div>
        <Button variant="secondary" onClick={() => setShowCreate((v) => !v)}>
          {t("dashboard.cohorts.newCohort")}
        </Button>
      </div>

      {showCreate && (
        <Card className={styles.createCard}>
          <div className={styles.createHeading}>
            {t("dashboard.cohorts.createHeading")}
          </div>
          <div className={styles.formBlock}>
            <TextInput
              id="cohort-name"
              label={t("dashboard.cohorts.nameLabel")}
              value={name}
              onChange={setName}
              placeholder={t("dashboard.cohorts.namePlaceholder")}
            />
            <TextInput
              id="cohort-year"
              label={t("dashboard.cohorts.yearLabel")}
              value={academicYear}
              onChange={setAcademicYear}
              placeholder={t("dashboard.cohorts.yearPlaceholder")}
            />
            <Button
              variant="primary"
              disabled={!name.trim() || creating}
              onClick={onCreate}
            >
              {t("dashboard.cohorts.createSubmit")}
            </Button>
          </div>
        </Card>
      )}

      {cohorts.length === 0 ? (
        <EmptyState
          icon="🎓"
          title={t("dashboard.cohorts.emptyTitle")}
          description={t("dashboard.cohorts.emptyDescription")}
        />
      ) : (
        <div className={styles.list}>
          {cohorts.map((cohort) => (
            <Card
              key={cohort.id}
              className={styles.cohortCard}
              onClick={() => onSelectCohort(cohort.id)}
            >
              <div className={styles.cohortMain}>
                <div className={styles.cohortName}>{cohort.name}</div>
                {cohort.academicYear && (
                  <div className={styles.cohortYear}>{cohort.academicYear}</div>
                )}
              </div>
              <Pill tone="count">
                {t("dashboard.cohorts.studentCount", {
                  count: cohort.studentCount,
                })}
              </Pill>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
