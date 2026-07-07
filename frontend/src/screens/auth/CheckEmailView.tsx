import { useTranslation } from "react-i18next";
import { Button } from "../../components/Button";
import { Callout } from "../../components/Callout";
import { Card } from "../../components/Card";
import { AuthShell } from "./AuthShell";
import styles from "./AuthShell.module.css";

export interface CheckEmailViewProps {
  loginName: string;
  onUseDifferentId: () => void;
}

export function CheckEmailView({ loginName, onUseDifferentId }: CheckEmailViewProps) {
  const { t } = useTranslation();
  return (
    <AuthShell>
      <Card>
        <div className={styles.cardHeading}>{t("auth.checkEmail.heading")}</div>
        <Callout tone="teal" style={{ marginBottom: 18 }}>
          {t("auth.checkEmail.calloutPre")}
          <strong>{loginName}</strong>
          {t("auth.checkEmail.calloutPost")}
        </Callout>
        <Button variant="ghost" onClick={onUseDifferentId}>
          {t("auth.checkEmail.useDifferentId")}
        </Button>
      </Card>
    </AuthShell>
  );
}
