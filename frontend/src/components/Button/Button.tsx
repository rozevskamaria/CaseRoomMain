import type { ButtonHTMLAttributes, CSSProperties, ReactNode } from "react";
import styles from "./Button.module.css";

export type ButtonVariant = "primary" | "secondary" | "ghost";

export interface ButtonProps {
  variant?: ButtonVariant;
  onClick?: ButtonHTMLAttributes<HTMLButtonElement>["onClick"];
  disabled?: boolean;
  type?: ButtonHTMLAttributes<HTMLButtonElement>["type"];
  children?: ReactNode;
  style?: CSSProperties;
  className?: string;
}

export function Button({
  variant = "primary",
  onClick,
  disabled,
  type = "button",
  children,
  style,
  className,
}: ButtonProps) {
  const classes = [styles.button, styles[variant], className]
    .filter(Boolean)
    .join(" ");
  return (
    <button
      type={type}
      className={classes}
      onClick={onClick}
      disabled={disabled}
      style={style}
    >
      {children}
    </button>
  );
}
