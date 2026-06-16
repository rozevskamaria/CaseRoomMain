import { Button } from "../../components/Button";
import { Callout } from "../../components/Callout";
import styles from "./ReflectionDone.module.css";

export interface ReflectionDoneProps {
  tutorText: string;
  onReturn: () => void;
}

export function ReflectionDone({ tutorText, onReturn }: ReflectionDoneProps) {
  return (
    <div className={styles.root}>
      <div className={styles.inner}>
        <h2 className={styles.heading}>Reflection complete</h2>
        <div className={styles.tutorBox}>{tutorText}</div>
        <Callout tone="teal" style={{ lineHeight: "normal", marginBottom: 24 }}>
          You can return to this case at any time, or explore another case from the library.
        </Callout>
        <Button variant="primary" onClick={onReturn}>
          Return to clinic
        </Button>
      </div>
    </div>
  );
}
