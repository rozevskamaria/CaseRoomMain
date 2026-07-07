import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../../components/Button";
import { LocaleSwitcher } from "../../components/LocaleSwitcher";
import { useLocale } from "../../i18n/useLocale";
import styles from "./DashboardShell.module.css";

export interface Crumb {
  label: string;
  onClick?: () => void;
}

export interface DashboardShellProps {
  crumbs: Crumb[];
  onBack?: () => void;
  onLogout?: () => void;
  sectionNav?: ReactNode;
  children: ReactNode;
}

export function DashboardShell({
  crumbs,
  onBack,
  onLogout,
  sectionNav,
  children,
}: DashboardShellProps) {
  const { t } = useTranslation();
  const { locale, setLocale } = useLocale();
  return (
    <div className={styles.root}>
      <div className={styles.column}>
        <div className={styles.topBar}>
          <LocaleSwitcher value={locale} onChange={setLocale} />
          {onLogout && (
            <Button variant="ghost" onClick={onLogout}>
              {t("dashboard.signOut")}
            </Button>
          )}
        </div>
        <div className={styles.header}>
          <div className={styles.logo}>{t("dashboard.logoLine")}</div>
          <h1 className={styles.heroTitle}>{t("dashboard.heroTitle")}</h1>
          <p className={styles.heroSub}>{t("dashboard.heroSub")}</p>
        </div>
        <nav className={styles.breadcrumb} aria-label="breadcrumb">
          {crumbs.map((crumb, index) => {
            const last = index === crumbs.length - 1;
            return (
              <span key={index} className={styles.crumbItem}>
                {crumb.onClick && !last ? (
                  <button
                    type="button"
                    className={styles.crumbLink}
                    onClick={crumb.onClick}
                  >
                    {crumb.label}
                  </button>
                ) : (
                  <span className={last ? styles.crumbCurrent : styles.crumbText}>
                    {crumb.label}
                  </span>
                )}
                {!last && <span className={styles.crumbSep}>/</span>}
              </span>
            );
          })}
        </nav>
        {sectionNav && <div className={styles.sectionNav}>{sectionNav}</div>}
        {onBack && (
          <div className={styles.backRow}>
            <Button variant="ghost" onClick={onBack}>
              {t("dashboard.back")}
            </Button>
          </div>
        )}
        {children}
      </div>
    </div>
  );
}

export function DashboardSpinner({ label }: { label?: string }) {
  const { t } = useTranslation();
  return (
    <div className={styles.spinnerRoot}>
      <div className={styles.spinner} />
      {label ?? t("dashboard.loading")}
    </div>
  );
}
