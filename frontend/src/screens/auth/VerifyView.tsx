import { useState } from "react";
import { useMutation } from "@apollo/client";
import { useTranslation } from "react-i18next";
import { Button } from "../../components/Button";
import { Callout } from "../../components/Callout";
import { Card } from "../../components/Card";
import { ConsumeMagicLinkMutation } from "../../graphql/authOperations";
import { AuthShell } from "./AuthShell";
import styles from "./AuthShell.module.css";

export interface VerifyViewProps {
  token: string | null;
  onConfirmed: () => void;
  onBackToLogin: () => void;
}

export function VerifyView({ token, onConfirmed, onBackToLogin }: VerifyViewProps) {
  const { t } = useTranslation();
  const [failed, setFailed] = useState(token === null);
  const [consumeMagicLink, { loading }] = useMutation(ConsumeMagicLinkMutation);

  const onConfirm = () => {
    if (token === null || loading) return;
    void consumeMagicLink({ variables: { token } }).then((result) => {
      if (result.data?.consumeMagicLink.ok) {
        onConfirmed();
      } else {
        setFailed(true);
      }
    });
  };

  if (failed) {
    return (
      <AuthShell>
        <Card>
          <div className={styles.cardHeading}>{t("auth.verify.linkHeading")}</div>
          <Callout tone="amber" style={{ marginBottom: 18 }}>
            {t("auth.verify.expired")}
          </Callout>
          <Button variant="primary" className={styles.fullWidth} onClick={onBackToLogin}>
            {t("auth.verify.requestNew")}
          </Button>
        </Card>
      </AuthShell>
    );
  }

  return (
    <AuthShell>
      <Card>
        <div className={styles.cardHeading}>{t("auth.verify.confirmHeading")}</div>
        <p className={styles.intro}>{t("auth.verify.confirmIntro")}</p>
        <Button
          variant="primary"
          className={styles.fullWidth}
          disabled={loading}
          onClick={onConfirm}
        >
          {t("auth.verify.confirm")}
        </Button>
      </Card>
    </AuthShell>
  );
}
