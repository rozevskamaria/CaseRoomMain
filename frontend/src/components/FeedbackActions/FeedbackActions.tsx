import { useTranslation } from "react-i18next";
import { Button } from "../Button";
import styles from "./FeedbackActions.module.css";

export interface FeedbackActionsProps {
  mode: string;
  onSeeNext: () => void;
  onReflect: () => void;
  onBrowse: () => void;
}

export function FeedbackActions({
  mode,
  onSeeNext,
  onReflect,
  onBrowse,
}: FeedbackActionsProps) {
  const { t } = useTranslation();
  return (
    <div className={styles.actions}>
      <Button variant="primary" onClick={onSeeNext}>
        {t("feedback.seeNext")}
      </Button>
      {mode !== "reflection" && (
        <Button variant="secondary" onClick={onReflect}>
          {t("feedback.reflectOnCase")}
        </Button>
      )}
      <Button variant="ghost" onClick={onBrowse}>
        {t("feedback.browseAll")}
      </Button>
    </div>
  );
}
