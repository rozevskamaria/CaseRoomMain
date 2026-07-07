import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@apollo/client";
import { useTranslation } from "react-i18next";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { TextInput } from "../../components/TextInput";
import { onlyDigits } from "../../lib/onlyDigits";
import {
  AddStudentToCohortMutation,
  CohortRosterQuery,
  CohortQuery,
  LookupStudentQuery,
} from "../../graphql/cohortOperations";
import styles from "./EnrollStudentForm.module.css";

export interface EnrollStudentFormProps {
  cohortId: string;
}

type Tone = "teal" | "amber" | "red";

const STATUS_TONE: Record<string, Tone> = {
  enrollable: "teal",
  already_enrolled: "amber",
  not_found: "red",
  not_a_student: "red",
};

export function EnrollStudentForm({ cohortId }: EnrollStudentFormProps) {
  const { t } = useTranslation();
  const [loginName, setLoginName] = useState("");
  const [debounced, setDebounced] = useState("");
  const [added, setAdded] = useState(false);

  const valid = loginName.length === 6;

  useEffect(() => {
    setAdded(false);
    if (!valid) {
      setDebounced("");
      return;
    }
    const handle = window.setTimeout(() => setDebounced(loginName), 250);
    return () => window.clearTimeout(handle);
  }, [loginName, valid]);

  const lookup = useQuery(LookupStudentQuery, {
    variables: { cohortId, loginName: debounced },
    skip: debounced.length !== 6,
    fetchPolicy: "network-only",
  });

  const [addStudent, addState] = useMutation(AddStudentToCohortMutation, {
    refetchQueries: [
      { query: CohortRosterQuery, variables: { cohortId } },
      { query: CohortQuery, variables: { id: cohortId } },
    ],
  });

  const lookupStatus =
    valid && debounced === loginName ? lookup.data?.lookupStudent.status : undefined;
  const lookupName = lookup.data?.lookupStudent.fullName ?? null;
  const checking = valid && lookup.loading && debounced === loginName;

  const canSubmit =
    valid && lookupStatus === "enrollable" && !addState.loading && !checking;

  const onSubmit = () => {
    if (!canSubmit) return;
    void addStudent({ variables: { cohortId, loginName } }).then((res) => {
      if (res.data?.addStudentToCohort.status === "enrolled") {
        setLoginName("");
        setDebounced("");
        setAdded(true);
      }
    });
  };

  const renderFeedback = () => {
    if (added) {
      return (
        <div className={`${styles.banner} ${styles.teal}`}>
          {t("dashboard.enroll.addedSuccess")}
        </div>
      );
    }
    if (!valid) return null;
    if (checking) {
      return <div className={styles.checking}>{t("dashboard.enroll.checking")}</div>;
    }
    if (lookupStatus === undefined) return null;
    const tone = STATUS_TONE[lookupStatus] ?? "red";
    let message: string;
    if (lookupStatus === "enrollable") {
      message = lookupName
        ? t("dashboard.enroll.enrollableLabel", { name: lookupName })
        : t("dashboard.enroll.enrollableNoName");
    } else if (lookupStatus === "already_enrolled") {
      message = t("dashboard.enroll.alreadyEnrolled");
    } else if (lookupStatus === "not_a_student") {
      message = t("dashboard.enroll.notAStudent");
    } else {
      message = t("dashboard.enroll.notFound");
    }
    return <div className={`${styles.banner} ${styles[tone]}`}>{message}</div>;
  };

  return (
    <Card className={styles.card}>
      <div className={styles.heading}>{t("dashboard.enroll.heading")}</div>
      <div className={styles.formBlock}>
        <TextInput
          id="enroll-id"
          label={t("dashboard.enroll.idLabel")}
          value={loginName}
          onChange={(value) => setLoginName(onlyDigits(value))}
          placeholder={t("dashboard.enroll.idPlaceholder")}
          suffix="@rsu.edu.lv"
          inputMode="numeric"
          maxLength={6}
        />
        {renderFeedback()}
        {addState.error && !added && (
          <div className={`${styles.banner} ${styles.red}`}>
            {t("dashboard.enroll.errorGeneric")}
          </div>
        )}
        <Button variant="primary" disabled={!canSubmit} onClick={onSubmit}>
          {t("dashboard.enroll.submit")}
        </Button>
      </div>
    </Card>
  );
}
