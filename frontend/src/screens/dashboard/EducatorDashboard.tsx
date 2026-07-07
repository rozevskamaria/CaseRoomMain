import { useCallback, useReducer } from "react";
import { useMutation } from "@apollo/client";
import { useTranslation } from "react-i18next";
import { LogoutMutation } from "../../graphql/authOperations";
import type { MeQuery } from "../../gql/graphql";
import { TabBar } from "../../components/TabBar";
import { DashboardShell } from "./DashboardShell";
import type { Crumb } from "./DashboardShell";
import { CohortsView } from "./CohortsView";
import { CohortDetailView } from "./CohortDetailView";
import { StudentReviewView } from "./StudentReviewView";
import { AttemptReplay } from "./AttemptReplay";
import { CasesView } from "./authoring/CasesView";
import { CaseEditor } from "./authoring/CaseEditor";

export type Me = NonNullable<MeQuery["me"]>;

export interface EducatorDashboardProps {
  me: Me;
  onLogout?: () => void;
}

type Section = "cohorts" | "cases";

interface NavState {
  section: Section;
  cohortId: string | null;
  studentId: string | null;
  attemptId: string | null;
  caseVersionId: string | null;
}

type NavAction =
  | { type: "SELECT_COHORT"; cohortId: string }
  | { type: "SELECT_STUDENT"; studentId: string }
  | { type: "SELECT_ATTEMPT"; attemptId: string }
  | { type: "TO_COHORTS" }
  | { type: "TO_COHORT" }
  | { type: "TO_STUDENT" }
  | { type: "TO_CASES" }
  | { type: "TO_CASE_LIST" }
  | { type: "SELECT_CASE_DRAFT"; caseVersionId: string };

function navReducer(state: NavState, action: NavAction): NavState {
  switch (action.type) {
    case "SELECT_COHORT":
      return { ...state, cohortId: action.cohortId, studentId: null, attemptId: null };
    case "SELECT_STUDENT":
      return { ...state, studentId: action.studentId, attemptId: null };
    case "SELECT_ATTEMPT":
      return { ...state, attemptId: action.attemptId };
    case "TO_COHORTS":
      return { ...state, section: "cohorts", cohortId: null, studentId: null, attemptId: null };
    case "TO_COHORT":
      return { ...state, studentId: null, attemptId: null };
    case "TO_STUDENT":
      return { ...state, attemptId: null };
    case "TO_CASES":
      return { ...INITIAL_NAV, section: "cases" };
    case "TO_CASE_LIST":
      return { ...state, section: "cases", caseVersionId: null };
    case "SELECT_CASE_DRAFT":
      return { ...state, section: "cases", caseVersionId: action.caseVersionId };
    default:
      return state;
  }
}

const INITIAL_NAV: NavState = {
  section: "cohorts",
  cohortId: null,
  studentId: null,
  attemptId: null,
  caseVersionId: null,
};

export function EducatorDashboard({ me, onLogout }: EducatorDashboardProps) {
  const { t } = useTranslation();
  const [nav, dispatch] = useReducer(navReducer, INITIAL_NAV);
  const [logout] = useMutation(LogoutMutation);
  const isAdmin = me.role === "admin";
  const isStaff = me.role === "staff" || isAdmin;

  const handleLogout = useCallback(() => {
    void logout().finally(() => {
      onLogout?.();
    });
  }, [logout, onLogout]);

  const crumbs: Crumb[] = [];
  if (nav.section === "cases") {
    crumbs.push({
      label: t("dashboard.breadcrumb.cases"),
      onClick: () => dispatch({ type: "TO_CASE_LIST" }),
    });
    if (nav.caseVersionId) {
      crumbs.push({ label: t("dashboard.breadcrumb.editor") });
    }
  } else {
    crumbs.push({
      label: t("dashboard.breadcrumb.cohorts"),
      onClick: () => dispatch({ type: "TO_COHORTS" }),
    });
    if (nav.cohortId) {
      crumbs.push({
        label: t("dashboard.breadcrumb.roster"),
        onClick: () => dispatch({ type: "TO_COHORT" }),
      });
    }
    if (nav.studentId) {
      crumbs.push({
        label: t("dashboard.breadcrumb.attempts"),
        onClick: () => dispatch({ type: "TO_STUDENT" }),
      });
    }
    if (nav.attemptId) {
      crumbs.push({ label: t("dashboard.breadcrumb.replay") });
    }
  }

  let onBack: (() => void) | undefined;
  if (nav.section === "cases") {
    if (nav.caseVersionId) onBack = () => dispatch({ type: "TO_CASE_LIST" });
  } else if (nav.attemptId) {
    onBack = () => dispatch({ type: "TO_STUDENT" });
  } else if (nav.studentId) {
    onBack = () => dispatch({ type: "TO_COHORT" });
  } else if (nav.cohortId) {
    onBack = () => dispatch({ type: "TO_COHORTS" });
  }

  let content;
  if (nav.section === "cases") {
    if (nav.caseVersionId) {
      content = (
        <CaseEditor
          versionId={nav.caseVersionId}
          canPublish={isStaff}
          onDiscarded={() => dispatch({ type: "TO_CASE_LIST" })}
        />
      );
    } else {
      content = (
        <CasesView
          onOpenDraft={(caseVersionId) =>
            dispatch({ type: "SELECT_CASE_DRAFT", caseVersionId })
          }
        />
      );
    }
  } else if (nav.cohortId && nav.studentId && nav.attemptId) {
    content = <AttemptReplay attemptId={nav.attemptId} />;
  } else if (nav.cohortId && nav.studentId) {
    content = (
      <StudentReviewView
        cohortId={nav.cohortId}
        studentId={nav.studentId}
        onSelectAttempt={(attemptId) =>
          dispatch({ type: "SELECT_ATTEMPT", attemptId })
        }
      />
    );
  } else if (nav.cohortId) {
    content = (
      <CohortDetailView
        cohortId={nav.cohortId}
        isAdmin={isAdmin}
        onReviewStudent={(studentId) =>
          dispatch({ type: "SELECT_STUDENT", studentId })
        }
      />
    );
  } else {
    content = (
      <CohortsView
        onSelectCohort={(cohortId) =>
          dispatch({ type: "SELECT_COHORT", cohortId })
        }
      />
    );
  }

  const sectionNav = isStaff ? (
    <TabBar
      tabs={[
        { key: "cohorts", label: t("dashboard.section.cohorts") },
        { key: "cases", label: t("dashboard.section.cases") },
      ]}
      active={nav.section}
      onChange={(key) =>
        dispatch(key === "cases" ? { type: "TO_CASES" } : { type: "TO_COHORTS" })
      }
    />
  ) : undefined;

  return (
    <DashboardShell
      crumbs={crumbs}
      onBack={onBack}
      onLogout={onLogout ? handleLogout : undefined}
      sectionNav={sectionNav}
    >
      {content}
    </DashboardShell>
  );
}
