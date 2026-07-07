import { useState } from "react";
import { useMutation } from "@apollo/client";
import { useTranslation } from "react-i18next";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { TextInput } from "../../components/TextInput";
import { RegisterStudentMutation } from "../../graphql/authOperations";
import { AuthShell } from "./AuthShell";
import { CheckEmailView } from "./CheckEmailView";
import styles from "./AuthShell.module.css";

export interface RegisterViewProps {
  onGoToLogin: () => void;
}

function onlyDigits(value: string): string {
  return value.replace(/\D/g, "").slice(0, 6);
}

export function RegisterView({ onGoToLogin }: RegisterViewProps) {
  const { t } = useTranslation();
  const [loginName, setLoginName] = useState("");
  const [fullName, setFullName] = useState("");
  const [sent, setSent] = useState(false);
  const [registerStudent, { loading }] = useMutation(RegisterStudentMutation);

  const valid = loginName.length === 6;

  if (sent) {
    return (
      <CheckEmailView loginName={loginName} onUseDifferentId={() => setSent(false)} />
    );
  }

  const onSubmit = () => {
    if (!valid || loading) return;
    const trimmed = fullName.trim();
    void registerStudent({
      variables: { loginName, fullName: trimmed === "" ? null : trimmed },
    }).then(() => setSent(true));
  };

  return (
    <AuthShell>
      <Card>
        <div className={styles.cardHeading}>{t("auth.register.heading")}</div>
        <p className={styles.intro}>{t("auth.register.intro")}</p>
        <div className={styles.formBlock}>
          <TextInput
            id="register-id"
            label={t("auth.register.idLabel")}
            value={loginName}
            onChange={(value) => setLoginName(onlyDigits(value))}
            placeholder={t("auth.register.idPlaceholder")}
            suffix="@rsu.edu.lv"
            inputMode="numeric"
            maxLength={6}
            autoFocus
          />
          <TextInput
            id="register-name"
            label={t("auth.register.nameLabel")}
            value={fullName}
            onChange={setFullName}
            placeholder={t("auth.register.namePlaceholder")}
          />
          <Button
            variant="primary"
            className={styles.fullWidth}
            disabled={!valid || loading}
            onClick={onSubmit}
          >
            {t("auth.register.submit")}
          </Button>
        </div>
        <div className={styles.altRow}>
          {t("auth.register.altPrompt")}
          <Button variant="ghost" onClick={onGoToLogin}>
            {t("auth.register.altAction")}
          </Button>
        </div>
      </Card>
    </AuthShell>
  );
}
