import styles from "./InfoBox.module.css";

export type InfoBoxTone = "surface" | "navyPale";

export interface InfoBoxProps {
  title: string;
  text: string;
  tone: InfoBoxTone;
}

export function InfoBox({ title, text, tone }: InfoBoxProps) {
  if (tone === "navyPale") {
    return (
      <div className={styles.navyPaleBox}>
        <div className={styles.innerTitle}>{title}</div>
        <div className={styles.innerText}>{text}</div>
      </div>
    );
  }
  return (
    <div className={styles.surfaceWrap}>
      <h3 className={styles.outerTitle}>{title}</h3>
      <div className={styles.surfaceBox}>{text}</div>
    </div>
  );
}
