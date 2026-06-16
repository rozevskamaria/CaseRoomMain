import { flagRow } from "../../lib/labText";
import type { LabLine } from "../../lib/labText";
import { FLAG_STYLE } from "../../styles/flagStyle";
import type { FlagKey } from "../../styles/flagStyle";
import { LabNoteRow } from "../LabNoteRow";
import { LabFlagBadge } from "../LabFlagBadge";
import styles from "./LabTable.module.css";

export interface LabTableProps {
  rows: LabLine[];
}

export function LabTable({ rows }: LabTableProps) {
  return (
    <table className={styles.table}>
      <thead>
        <tr className={styles.headRow}>
          <th className={`${styles.th} ${styles.thParam}`}>Parameter</th>
          <th className={styles.th}>Result</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, ri) => {
          if (row.type === "note") {
            return <LabNoteRow key={ri} text={row.text} />;
          }
          const flag = flagRow(row.value) as FlagKey;
          const fs = FLAG_STYLE[flag];
          const rowBg =
            fs.bg !== "transparent" ? fs.bg : ri % 2 === 0 ? "#ffffff" : "#F8FAFC";
          return (
            <tr key={ri} style={{ background: rowBg }}>
              <td className={styles.paramCell}>{row.param}</td>
              <td
                className={styles.valueCell}
                style={{
                  color: fs.text,
                  fontWeight: fs.bg !== "transparent" ? 600 : 400,
                }}
              >
                {row.value}
                <LabFlagBadge flag={flag} />
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
