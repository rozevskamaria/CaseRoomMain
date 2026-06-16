import styles from "./LabNoteRow.module.css";

export interface LabNoteRowProps {
  text: string;
}

export function LabNoteRow({ text }: LabNoteRowProps) {
  return (
    <tr className={styles.row}>
      <td colSpan={2} className={styles.cell}>
        ⚠ {text}
      </td>
    </tr>
  );
}
