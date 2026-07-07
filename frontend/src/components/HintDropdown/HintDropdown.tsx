import type { CSSProperties } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../Button";
import styles from "./HintDropdown.module.css";

export interface HintDropdownProps {
  open: boolean;
  hintsUsed: number;
  onGetHint: () => void;
  style?: CSSProperties;
  className?: string;
}

export function HintDropdown({
  open,
  hintsUsed,
  onGetHint,
  style,
  className,
}: HintDropdownProps) {
  const { t } = useTranslation();
  if (!open) return null;
  const classes = [styles.panel, className].filter(Boolean).join(" ");
  return (
    <div className={classes} style={style}>
      <div className={styles.title}>{t("hint.dropdownTitle")}</div>
      <div className={styles.desc}>{t("hint.dropdownDesc")}</div>
      <Button
        variant="primary"
        style={{ width: "100%", fontSize: 13 }}
        onClick={onGetHint}
      >
        {t("hint.getHint")}
      </Button>
      {hintsUsed > 0 && (
        <div className={styles.usedCount}>
          {t("hint.usedCount", { count: hintsUsed })}
        </div>
      )}
    </div>
  );
}
