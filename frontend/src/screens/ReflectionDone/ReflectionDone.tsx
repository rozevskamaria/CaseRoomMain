import { useTranslation } from "react-i18next";
import { Button } from "../../components/Button";
import { Callout } from "../../components/Callout";
import styles from "./ReflectionDone.module.css";

export interface ReflectionDoneProps {
  tutorText: string;
  onReturn: () => void;
}

export function ReflectionDone({ tutorText, onReturn }: ReflectionDoneProps) {
  const { t } = useTranslation();
  return (
    <div className={styles.root}>
      <div className={styles.inner}>
        <h2 className={styles.heading}>{t("reflectionDone.heading")}</h2>
        <div className={styles.tutorBox}>{tutorText}</div>
        <Callout tone="teal" style={{ lineHeight: "normal", marginBottom: 24 }}>
          {t("reflectionDone.callout")}
        </Callout>
        <Button variant="primary" onClick={onReturn}>
          {t("reflectionDone.returnToClinic")}
        </Button>
      </div>
    </div>
  );
}
