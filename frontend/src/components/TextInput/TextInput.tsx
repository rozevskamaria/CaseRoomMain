import type { CSSProperties, InputHTMLAttributes, ReactNode } from "react";
import styles from "./TextInput.module.css";

export interface TextInputProps {
  id?: string;
  label?: ReactNode;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  suffix?: ReactNode;
  inputMode?: InputHTMLAttributes<HTMLInputElement>["inputMode"];
  maxLength?: number;
  autoFocus?: boolean;
  disabled?: boolean;
  style?: CSSProperties;
  className?: string;
}

export function TextInput({
  id,
  label,
  value,
  onChange,
  placeholder,
  suffix,
  inputMode,
  maxLength,
  autoFocus,
  disabled,
  style,
  className,
}: TextInputProps) {
  const classes = [styles.field, className].filter(Boolean).join(" ");
  return (
    <div className={classes} style={style}>
      {label !== undefined && (
        <label className={styles.label} htmlFor={id}>
          {label}
        </label>
      )}
      <div className={styles.inputRow}>
        <input
          id={id}
          className={styles.input}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          inputMode={inputMode}
          maxLength={maxLength}
          autoFocus={autoFocus}
          disabled={disabled}
        />
        {suffix !== undefined && <div className={styles.suffix}>{suffix}</div>}
      </div>
    </div>
  );
}
