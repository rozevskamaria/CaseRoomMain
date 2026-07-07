import { useTranslation } from "react-i18next";
import { Button } from "../../components/Button";
import { Pill } from "../../components/Pill";
import styles from "./RosterTable.module.css";

export interface RosterRow {
  id: string;
  loginName: string;
  fullName: string | null;
  joinedAt: string;
}

export interface RosterTableProps {
  rows: RosterRow[];
  onReview: (studentId: string) => void;
  onRemove: (studentId: string) => void;
}

function formatJoined(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString();
}

export function RosterTable({ rows, onReview, onRemove }: RosterTableProps) {
  const { t } = useTranslation();
  return (
    <table className={styles.table}>
      <thead>
        <tr className={styles.headRow}>
          <th className={`${styles.th} ${styles.thId}`}>
            {t("dashboard.roster.colId")}
          </th>
          <th className={styles.th}>{t("dashboard.roster.colName")}</th>
          <th className={styles.th}>{t("dashboard.roster.colStatus")}</th>
          <th className={styles.th}>{t("dashboard.roster.colJoined")}</th>
          <th className={styles.th} />
        </tr>
      </thead>
      <tbody>
        {rows.map((row, ri) => (
          <tr
            key={row.id}
            className={styles.bodyRow}
            style={{ background: ri % 2 === 0 ? "#ffffff" : "#F8FAFC" }}
          >
            <td className={styles.idCell}>{row.loginName}</td>
            <td className={styles.cell}>
              {row.fullName ?? t("dashboard.roster.noName")}
            </td>
            <td className={styles.cell}>
              <Pill tone="score" value="Excellent">
                {t("dashboard.roster.statusActive")}
              </Pill>
            </td>
            <td className={styles.cell}>{formatJoined(row.joinedAt)}</td>
            <td className={`${styles.cell} ${styles.actionCell}`}>
              <Button variant="ghost" onClick={() => onReview(row.id)}>
                {t("dashboard.roster.review")}
              </Button>
              <Button variant="ghost" onClick={() => onRemove(row.id)}>
                {t("dashboard.roster.remove")}
              </Button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
