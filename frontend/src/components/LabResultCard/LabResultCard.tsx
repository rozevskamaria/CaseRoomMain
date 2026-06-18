import { parseLabText } from "../../lib/labText";
import type { LabLine } from "../../lib/labText";
import { LabTable } from "../LabTable";
import styles from "./LabResultCard.module.css";

export interface LabResultCardProps {
  header?: string;
  text?: string;
  rows?: LabLine[];
}

function resolve(props: LabResultCardProps): { header: string; rows: LabLine[] } {
  if (props.rows) {
    return { header: props.header ?? "", rows: props.rows };
  }
  const raw = props.text ?? "";
  if (props.header === undefined) {
    const [header, ...rest] = raw.replace("__LAB__", "").split("\n");
    const bodyText = rest.join(" ");
    return { header: header ?? "", rows: parseLabText(bodyText) };
  }
  return { header: props.header, rows: parseLabText(raw) };
}

export function LabResultCard(props: LabResultCardProps) {
  const { header, rows } = resolve(props);
  const hasRows = rows.some((r) => r.type === "row");
  return (
    <div className={styles.wrap}>
      <div className={styles.card}>
        <div className={styles.header}>
          <span className={styles.icon}>🔬</span>
          <span className={styles.title}>{header}</span>
        </div>
        {hasRows && <LabTable rows={rows} />}
        {!hasRows && (
          <div className={styles.textBlock}>
            {rows.map((row, ri) => (
              <div key={ri} className={styles.textLine}>
                {row.type === "note" ? row.text : ""}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
