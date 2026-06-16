import { FLAG_STYLE } from "../../styles/flagStyle";
import type { FlagKey } from "../../styles/flagStyle";
import styles from "./LabFlagBadge.module.css";

export interface LabFlagBadgeProps {
  flag: FlagKey;
}

export function LabFlagBadge({ flag }: LabFlagBadgeProps) {
  const fs = FLAG_STYLE[flag];
  if (!fs.badge) {
    return null;
  }
  return (
    <span
      className={styles.badge}
      style={{ background: fs.badgeBg ?? undefined, color: fs.badgeText ?? undefined }}
    >
      {fs.badge}
    </span>
  );
}
