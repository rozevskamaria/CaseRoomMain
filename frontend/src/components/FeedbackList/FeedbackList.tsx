import styles from "./FeedbackList.module.css";

export type FeedbackListVariant = "strip" | "boxedBullets" | "bareBullets";
export type FeedbackListTone =
  | "teal"
  | "amber"
  | "navy"
  | "navyLight";

export interface FeedbackListProps {
  title: string;
  items: string[];
  variant: FeedbackListVariant;
  tone: FeedbackListTone;
  className?: string;
}

function headingToneClass(tone: FeedbackListTone): string {
  if (tone === "teal") return styles.headingTeal;
  if (tone === "amber") return styles.headingAmber;
  return styles.headingNavy;
}

function accentToneClass(tone: FeedbackListTone): string {
  if (tone === "teal") return styles.accentTeal;
  if (tone === "amber") return styles.accentAmber;
  if (tone === "navyLight") return styles.accentNavyLight;
  return styles.accentNavy;
}

export function FeedbackList({
  title,
  items,
  variant,
  tone,
  className,
}: FeedbackListProps) {
  const headingClass =
    variant === "bareBullets" ? styles.headingSmall : styles.heading;
  const items_ = items;

  if (variant === "strip") {
    return (
      <div className={className}>
        <h3 className={[headingClass, headingToneClass(tone)].join(" ")}>
          {title}
        </h3>
        {items_.map((item, i) => (
          <div
            key={i}
            className={[styles.strip, accentToneClass(tone)].join(" ")}
          >
            {item}
          </div>
        ))}
      </div>
    );
  }

  if (variant === "boxedBullets") {
    return (
      <div className={className}>
        <h3 className={[headingClass, headingToneClass(tone)].join(" ")}>
          {title}
        </h3>
        <div className={styles.box}>
          {items_.map((item, i) => (
            <div
              key={i}
              className={[styles.boxedBullet, accentToneClass(tone)].join(" ")}
            >
              • {item}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <h3 className={[headingClass, headingToneClass(tone)].join(" ")}>
        {title}
      </h3>
      {items_.map((item, i) => (
        <div
          key={i}
          className={[styles.bareBullet, accentToneClass(tone)].join(" ")}
        >
          • {item}
        </div>
      ))}
    </div>
  );
}
