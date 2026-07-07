import { useState } from "react";
import { useMutation } from "@apollo/client";
import { useTranslation } from "react-i18next";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { TextInput } from "../../components/TextInput";
import { RequestLoginLinkMutation } from "../../graphql/authOperations";
import { onlyDigits } from "../../lib/onlyDigits";
import { AuthShell } from "./AuthShell";
import { CheckEmailView } from "./CheckEmailView";
import { DevLoginPanel } from "./DevLoginPanel";
import styles from "./AuthShell.module.css";

export interface LoginViewProps {
  onGoToRegister: () => void;
  onAuthed: () => void;
}

export function LoginView({ onGoToRegister, onAuthed }: LoginViewProps) {
  const { t } = useTranslation();
  const [loginName, setLoginName] = useState("");
  const [sent, setSent] = useState(false);
  const [requestLoginLink, { loading }] = useMutation(RequestLoginLinkMutation);

  const valid = loginName.length === 6;

  if (sent) {
    return (
      <CheckEmailView
        loginName={loginName}
        onUseDifferentId={() => setSent(false)}
      />
    );
  }

  const onSubmit = () => {
    if (!valid || loading) return;
    void requestLoginLink({ variables: { loginName } }).then(() => setSent(true));
  };

  return (
    <AuthShell>
      <Card>
        <div className={styles.cardHeading}>{t("auth.signIn.heading")}</div>
        <p className={styles.intro}>{t("auth.signIn.intro")}</p>
        <div className={styles.formBlock}>
          <TextInput
            id="login-id"
            label={t("auth.signIn.idLabel")}
            value={loginName}
            onChange={(value) => setLoginName(onlyDigits(value))}
            placeholder={t("auth.signIn.idPlaceholder")}
            suffix="@rsu.edu.lv"
            inputMode="numeric"
            maxLength={6}
            autoFocus
          />
          <Button
            variant="primary"
            className={styles.fullWidth}
            disabled={!valid || loading}
            onClick={onSubmit}
          >
            {t("auth.signIn.submit")}
          </Button>
        </div>
        <div className={styles.altRow}>
          {t("auth.signIn.altPrompt")}
          <Button variant="ghost" onClick={onGoToRegister}>
            {t("auth.signIn.altAction")}
          </Button>
        </div>
      </Card>
      <DevLoginPanel onAuthed={onAuthed} />
    </AuthShell>
  );
}
