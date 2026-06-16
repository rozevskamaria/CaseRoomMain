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
  return (
    <div className={styles.actions}>
      <Button variant="primary" onClick={onSeeNext}>
        See next patient
      </Button>
      {mode !== "reflection" && (
        <Button variant="secondary" onClick={onReflect}>
          Reflect on this case
        </Button>
      )}
      <Button variant="ghost" onClick={onBrowse}>
        Browse all cases
      </Button>
    </div>
  );
}
