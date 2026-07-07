import { useState } from "react";
import { useMutation, useQuery } from "@apollo/client";
import { useTranslation } from "react-i18next";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { TabBar } from "../../components/TabBar";
import { TextInput } from "../../components/TextInput";
import { CASE_LIST } from "../../content/caseList";
import {
  AssignStaffToCohortMutation,
  AssignmentsForCohortQuery,
  CohortAuditLogQuery,
  CohortQuery,
  CohortRosterQuery,
  CreateAssignmentMutation,
  RemoveStudentFromCohortMutation,
} from "../../graphql/cohortOperations";
import { DashboardSpinner } from "./DashboardShell";
import { EnrollStudentForm } from "./EnrollStudentForm";
import { RosterTable } from "./RosterTable";
import { CohortAnalyticsPanel } from "./analytics";
import styles from "./CohortDetailView.module.css";

const MODES = ["practice", "exam", "reflection"] as const;
type CohortTab = "manage" | "analytics";

export interface CohortDetailViewProps {
  cohortId: string;
  isAdmin: boolean;
  onReviewStudent: (studentId: string) => void;
}

function modeLabel(t: (key: string) => string, mode: string): string {
  if (mode === "practice") return t("chat.modePractice");
  if (mode === "exam") return t("chat.modeExam");
  if (mode === "reflection") return t("chat.modeReflection");
  return mode;
}

export function CohortDetailView({
  cohortId,
  isAdmin,
  onReviewStudent,
}: CohortDetailViewProps) {
  const { t } = useTranslation();
  const cohortQuery = useQuery(CohortQuery, { variables: { id: cohortId } });
  const rosterQuery = useQuery(CohortRosterQuery, {
    variables: { cohortId },
    fetchPolicy: "cache-and-network",
  });
  const assignmentsQuery = useQuery(AssignmentsForCohortQuery, {
    variables: { cohortId },
  });

  const [removeStudent] = useMutation(RemoveStudentFromCohortMutation, {
    refetchQueries: [
      { query: CohortRosterQuery, variables: { cohortId } },
      { query: CohortQuery, variables: { id: cohortId } },
    ],
  });
  const [createAssignment, createAssignmentState] = useMutation(
    CreateAssignmentMutation,
    {
      refetchQueries: [
        { query: AssignmentsForCohortQuery, variables: { cohortId } },
      ],
    },
  );

  const [tab, setTab] = useState<CohortTab>("manage");
  const [showEnroll, setShowEnroll] = useState(false);
  const [caseId, setCaseId] = useState(CASE_LIST[0]?.id ?? "");
  const [mode, setMode] = useState<string>(MODES[0]);
  const [dueAt, setDueAt] = useState("");

  const cohort = cohortQuery.data?.cohort;
  const roster = rosterQuery.data?.cohortRoster ?? [];
  const assignments = assignmentsQuery.data?.assignmentsForCohort ?? [];

  if (cohortQuery.loading && cohortQuery.data === undefined) {
    return <DashboardSpinner />;
  }

  const onRemove = (studentId: string) => {
    if (!window.confirm(t("dashboard.roster.removeConfirm"))) return;
    void removeStudent({ variables: { cohortId, studentId } });
  };

  const onCreateAssignment = () => {
    if (!caseId || createAssignmentState.loading) return;
    void createAssignment({
      variables: {
        input: {
          cohortId,
          caseId,
          mode,
          dueAt: dueAt ? new Date(dueAt).toISOString() : null,
        },
      },
    }).then(() => setDueAt(""));
  };

  return (
    <div className={styles.view}>
      <h2 className={styles.cohortName}>{cohort?.name}</h2>
      {cohort?.academicYear && (
        <div className={styles.cohortYear}>{cohort.academicYear}</div>
      )}

      <TabBar
        tabs={[
          { key: "manage", label: t("dashboard.cohort.tabManage") },
          { key: "analytics", label: t("dashboard.cohort.tabAnalytics") },
        ]}
        active={tab}
        onChange={(key) => setTab(key as CohortTab)}
      />

      {tab === "analytics" ? (
        <CohortAnalyticsPanel cohortId={cohortId} />
      ) : (
        <>
      <section className={styles.section}>
        <div className={styles.sectionHead}>
          <h3 className={styles.sectionHeading}>
            {t("dashboard.roster.studentsHeading")}
          </h3>
          <Button variant="secondary" onClick={() => setShowEnroll((v) => !v)}>
            {showEnroll
              ? t("dashboard.enroll.toggleHide")
              : t("dashboard.enroll.toggleShow")}
          </Button>
        </div>

        {showEnroll && <EnrollStudentForm cohortId={cohortId} />}

        {roster.length === 0 ? (
          <EmptyState
            icon="👥"
            title={t("dashboard.roster.emptyTitle")}
            description={t("dashboard.roster.emptyDescription")}
          />
        ) : (
          <RosterTable
            rows={roster.map((row) => ({
              id: row.user.id,
              loginName: row.user.loginName,
              fullName: row.user.fullName ?? null,
              joinedAt: row.joinedAt,
            }))}
            onReview={onReviewStudent}
            onRemove={onRemove}
          />
        )}
      </section>

      <section className={styles.section}>
        <h3 className={styles.sectionHeading}>
          {t("dashboard.assignments.heading")}
        </h3>
        {assignments.length === 0 ? (
          <p className={styles.emptyText}>
            {t("dashboard.assignments.emptyDescription")}
          </p>
        ) : (
          <div className={styles.assignmentList}>
            {assignments.map((assignment) => {
              const caseMeta = CASE_LIST.find((c) => c.id === assignment.caseId);
              return (
                <Card key={assignment.id} className={styles.assignmentCard}>
                  <div className={styles.assignmentTitle}>
                    {assignment.title ?? caseMeta?.title ?? assignment.caseId}
                  </div>
                  <div className={styles.assignmentMeta}>
                    {modeLabel(t, assignment.mode)}
                    {" · "}
                    {assignment.dueAt
                      ? t("dashboard.assignments.due", {
                          date: new Date(assignment.dueAt).toLocaleDateString(),
                        })
                      : t("dashboard.assignments.noDue")}
                  </div>
                </Card>
              );
            })}
          </div>
        )}

        <Card className={styles.createCard}>
          <div className={styles.createHeading}>
            {t("dashboard.assignments.createHeading")}
          </div>
          <div className={styles.formBlock}>
            <label className={styles.fieldLabel} htmlFor="assign-case">
              {t("dashboard.assignments.caseLabel")}
            </label>
            <select
              id="assign-case"
              className={styles.select}
              value={caseId}
              onChange={(event) => setCaseId(event.target.value)}
            >
              {CASE_LIST.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </select>

            <label className={styles.fieldLabel} htmlFor="assign-mode">
              {t("dashboard.assignments.modeLabel")}
            </label>
            <select
              id="assign-mode"
              className={styles.select}
              value={mode}
              onChange={(event) => setMode(event.target.value)}
            >
              {MODES.map((m) => (
                <option key={m} value={m}>
                  {modeLabel(t, m)}
                </option>
              ))}
            </select>

            <label className={styles.fieldLabel} htmlFor="assign-due">
              {t("dashboard.assignments.dueLabel")}
            </label>
            <input
              id="assign-due"
              type="date"
              className={styles.select}
              value={dueAt}
              onChange={(event) => setDueAt(event.target.value)}
            />

            <Button
              variant="primary"
              disabled={!caseId || createAssignmentState.loading}
              onClick={onCreateAssignment}
            >
              {t("dashboard.assignments.createSubmit")}
            </Button>
          </div>
        </Card>
      </section>

      {isAdmin && (
        <>
          <StaffPanel cohortId={cohortId} staff={cohort?.staff ?? []} />
          <AuditPanel cohortId={cohortId} />
        </>
      )}
        </>
      )}
    </div>
  );
}

interface StaffMember {
  id: string;
  loginName: string;
  fullName?: string | null;
}

function StaffPanel({
  cohortId,
  staff,
}: {
  cohortId: string;
  staff: StaffMember[];
}) {
  const { t } = useTranslation();
  const [staffId, setStaffId] = useState("");
  const [assignStaff, { loading }] = useMutation(AssignStaffToCohortMutation, {
    refetchQueries: [{ query: CohortQuery, variables: { id: cohortId } }],
  });

  const onAssign = () => {
    if (!staffId.trim() || loading) return;
    void assignStaff({ variables: { cohortId, staffId: staffId.trim() } }).then(
      () => setStaffId(""),
    );
  };

  return (
    <section className={styles.section}>
      <h3 className={styles.sectionHeading}>{t("dashboard.staff.heading")}</h3>
      {staff.length === 0 ? (
        <p className={styles.emptyText}>{t("dashboard.staff.emptyDescription")}</p>
      ) : (
        <div className={styles.staffList}>
          {staff.map((member) => (
            <div key={member.id} className={styles.staffItem}>
              {member.fullName ?? member.loginName}
            </div>
          ))}
        </div>
      )}
      <Card className={styles.createCard}>
        <div className={styles.createHeading}>
          {t("dashboard.staff.assignHeading")}
        </div>
        <div className={styles.formBlock}>
          <TextInput
            id="assign-staff"
            label={t("dashboard.staff.idLabel")}
            value={staffId}
            onChange={setStaffId}
            placeholder={t("dashboard.staff.idPlaceholder")}
          />
          <Button variant="primary" disabled={!staffId.trim() || loading} onClick={onAssign}>
            {t("dashboard.staff.assignSubmit")}
          </Button>
        </div>
      </Card>
    </section>
  );
}

function AuditPanel({ cohortId }: { cohortId: string }) {
  const { t } = useTranslation();
  const { data } = useQuery(CohortAuditLogQuery, { variables: { cohortId } });
  const entries = data?.cohortAuditLog ?? [];

  return (
    <section className={styles.section}>
      <h3 className={styles.sectionHeading}>{t("dashboard.audit.heading")}</h3>
      {entries.length === 0 ? (
        <p className={styles.emptyText}>{t("dashboard.audit.emptyDescription")}</p>
      ) : (
        <table className={styles.auditTable}>
          <thead>
            <tr>
              <th className={styles.auditTh}>{t("dashboard.audit.colAction")}</th>
              <th className={styles.auditTh}>{t("dashboard.audit.colActor")}</th>
              <th className={styles.auditTh}>{t("dashboard.audit.colSubject")}</th>
              <th className={styles.auditTh}>{t("dashboard.audit.colWhen")}</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.id}>
                <td className={styles.auditTd}>{entry.action}</td>
                <td className={styles.auditTd}>{entry.actorId ?? "—"}</td>
                <td className={styles.auditTd}>{entry.subjectId ?? "—"}</td>
                <td className={styles.auditTd}>
                  {new Date(entry.createdAt).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
