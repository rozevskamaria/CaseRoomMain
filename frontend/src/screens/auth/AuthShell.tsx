import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { LocaleSwitcher } from "../../components/LocaleSwitcher";
import { useLocale } from "../../i18n/useLocale";
import styles from "./AuthShell.module.css";

export interface AuthShellProps {
  children: ReactNode;
}

export function AuthShell({ children }: AuthShellProps) {
  const { t } = useTranslation();
  const { locale, setLocale } = useLocale();
  return (
    <div className={styles.root}>
      <div className={styles.column}>
        <div className={styles.topBar}>
          <LocaleSwitcher value={locale} onChange={setLocale} />
        </div>
        <div className={styles.header}>
          <div className={styles.logo}>{t("auth.logoLine")}</div>
          <h1 className={styles.heroTitle}>{t("auth.heroTitle")}</h1>
          <p className={styles.heroSub}>{t("auth.heroSub")}</p>
        </div>
        {children}
      </div>
    </div>
  );
}

export function AuthSpinner({ label }: { label?: string }) {
  const { t } = useTranslation();
  return (
    <div className={styles.spinnerRoot}>
      <div className={styles.spinner} />
      {label ?? t("auth.loading")}
    </div>
  );
}
