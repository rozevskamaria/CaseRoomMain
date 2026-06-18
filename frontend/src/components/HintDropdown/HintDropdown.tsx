import type { CSSProperties } from "react";
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
  if (!open) return null;
  const classes = [styles.panel, className].filter(Boolean).join(" ");
  return (
    <div className={classes} style={style}>
      <div className={styles.title}>Ask for guidance</div>
      <div className={styles.desc}>
        The hint is personalised — it looks at what you have already asked and
        ordered, and points toward what might be missing.
      </div>
      <Button
        variant="primary"
        style={{ width: "100%", fontSize: 13 }}
        onClick={onGetHint}
      >
        Get a contextual hint →
      </Button>
      {hintsUsed > 0 && (
        <div className={styles.usedCount}>
          {hintsUsed} hint{hintsUsed > 1 ? "s" : ""} used this case
        </div>
      )}
    </div>
  );
}
