import { useState } from "react";
import { useMutation } from "@apollo/client";
import { useTranslation } from "react-i18next";
import { Button } from "../../components/Button";
import { TextInput } from "../../components/TextInput";
import { DevLoginMutation } from "../../graphql/authOperations";
import styles from "./AuthShell.module.css";

export interface DevLoginPanelProps {
  onAuthed: () => void;
}

export function DevLoginPanel({ onAuthed }: DevLoginPanelProps) {
  const { t } = useTranslation();
  const [loginName, setLoginName] = useState("100000");
  const [devLogin, { loading }] = useMutation(DevLoginMutation);

  if (!import.meta.env.DEV) return null;

  const onSubmit = () => {
    if (loginName.trim() === "" || loading) return;
    void devLogin({ variables: { loginName: loginName.trim() } }).then((result) => {
      if (result.data?.devLogin.ok) onAuthed();
    });
  };

  return (
    <div className={styles.devBlock}>
      <div className={styles.devLabel}>{t("auth.dev.label")}</div>
      <TextInput
        id="dev-login-id"
        value={loginName}
        onChange={setLoginName}
        placeholder={t("auth.dev.placeholder")}
      />
      <Button variant="secondary" disabled={loading} onClick={onSubmit}>
        {t("auth.dev.submit")}
      </Button>
    </div>
  );
}
