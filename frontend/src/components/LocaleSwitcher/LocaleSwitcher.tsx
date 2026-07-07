import type { CSSProperties } from "react";
import { useTranslation } from "react-i18next";
import { LOCALES } from "../../i18n/types";
import type { Locale } from "../../i18n/types";
import styles from "./LocaleSwitcher.module.css";

export interface LocaleSwitcherProps {
  value: Locale;
  onChange: (locale: Locale) => void;
  disabled?: boolean;
  style?: CSSProperties;
  className?: string;
}

export function LocaleSwitcher({
  value,
  onChange,
  disabled,
  style,
  className,
}: LocaleSwitcherProps) {
  const { t } = useTranslation();
  const classes = [styles.group, className].filter(Boolean).join(" ");
  return (
    <div className={classes} style={style} role="group" aria-label={t("locale.label")}>
      {LOCALES.map((locale) => {
        const active = locale === value;
        const optionClasses = [styles.option, active ? styles.active : ""]
          .filter(Boolean)
          .join(" ");
        return (
          <button
            key={locale}
            type="button"
            className={optionClasses}
            onClick={() => onChange(locale)}
            disabled={disabled}
            aria-pressed={active}
          >
            {t(`locale.${locale}`)}
          </button>
        );
      })}
    </div>
  );
}
