import { Pill } from "../Pill";
import styles from "./ScoreGrid.module.css";

export interface ScoreGridProps {
  scores: Record<string, string>;
}

function deCamelCase(domain: string): string {
  return domain.replace(/([A-Z])/g, " $1").trim();
}

export function ScoreGrid({ scores }: ScoreGridProps) {
  return (
    <div className={styles.scoreGrid}>
      {Object.entries(scores).map(([domain, score]) => (
        <div key={domain} className={styles.row}>
          <span className={styles.domain}>{deCamelCase(domain)}</span>
          <Pill tone="score" value={score}>
            {score}
          </Pill>
        </div>
      ))}
    </div>
  );
}
