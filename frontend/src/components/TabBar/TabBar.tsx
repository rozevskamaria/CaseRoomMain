import type { CSSProperties } from "react";
import styles from "./TabBar.module.css";

export interface TabBarItem {
  key: string;
  label: string;
  badge?: number;
}

export interface TabBarProps {
  tabs: TabBarItem[];
  active: string;
  onChange: (key: string) => void;
  style?: CSSProperties;
  className?: string;
}

export function TabBar({ tabs, active, onChange, style, className }: TabBarProps) {
  const classes = [styles.tabBar, className].filter(Boolean).join(" ");
  return (
    <div className={classes} style={style}>
      {tabs.map(({ key, label, badge }) => {
        const isActive = active === key;
        const tabClasses = [styles.tab, isActive ? styles.active : null]
          .filter(Boolean)
          .join(" ");
        return (
          <button key={key} onClick={() => onChange(key)} className={tabClasses}>
            {label}
            {badge !== undefined && badge > 0 && (
              <span className={styles.badge}>{badge}</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
