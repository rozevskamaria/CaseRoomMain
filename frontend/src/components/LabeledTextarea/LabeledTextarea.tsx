import type { ChangeEventHandler, CSSProperties, ReactNode } from "react";
import styles from "./LabeledTextarea.module.css";

export interface LabeledTextareaProps {
  label: ReactNode;
  value: string;
  onChange: ChangeEventHandler<HTMLTextAreaElement>;
  rows?: number;
  placeholder?: string;
  disabled?: boolean;
  style?: CSSProperties;
  className?: string;
  labelStyle?: CSSProperties;
}

export function LabeledTextarea({
  label,
  value,
  onChange,
  rows,
  placeholder,
  disabled,
  style,
  className,
  labelStyle,
}: LabeledTextareaProps) {
  const textareaClasses = [styles.textarea, className]
    .filter(Boolean)
    .join(" ");
  return (
    <div className={styles.field}>
      <div className={styles.label} style={labelStyle}>
        {label}
      </div>
      <textarea
        className={textareaClasses}
        value={value}
        onChange={onChange}
        rows={rows}
        placeholder={placeholder}
        disabled={disabled}
        style={style}
      />
    </div>
  );
}
