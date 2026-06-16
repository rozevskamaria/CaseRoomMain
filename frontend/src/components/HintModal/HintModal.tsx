import type { CSSProperties, ReactNode } from "react";
import styles from "./HintModal.module.css";

export interface HintModalProps {
  open: boolean;
  text: ReactNode;
  onClose: () => void;
  style?: CSSProperties;
  className?: string;
}

export function HintModal({
  open,
  text,
  onClose,
  style,
  className,
}: HintModalProps) {
  if (!open) return null;
  const classes = [styles.modal, className].filter(Boolean).join(" ");
  return (
    <>
      <div onClick={onClose} className={styles.backdrop} />
      <div className={classes} style={style}>
        <div className={styles.header}>
          <div className={styles.kicker}>🎓 Clinical tutor</div>
          <button onClick={onClose} className={styles.close}>
            ✕
          </button>
        </div>
        <div className={styles.body}>{text}</div>
        <button onClick={onClose} className={styles.gotIt}>
          Got it
        </button>
      </div>
    </>
  );
}
