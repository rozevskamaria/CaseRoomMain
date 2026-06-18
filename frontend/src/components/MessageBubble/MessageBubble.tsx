import type { CSSProperties } from "react";
import { LabResultCard } from "../LabResultCard";
import { TutorCard } from "../TutorCard";
import styles from "./MessageBubble.module.css";

export type MessageType =
  | "parent"
  | "tutor"
  | "student"
  | "safety"
  | "system"
  | "lab"
  | "lab_note"
  | "lab_tutor";

export interface MessageBubbleProps {
  type: MessageType;
  text: string;
  id?: string | number;
  style?: CSSProperties;
  className?: string;
}

type ChatType = "parent" | "tutor" | "safety" | "student" | "system";

const CHAT_CONFIG: Record<
  ChatType,
  { bubbleClass: string; label: string; alignClass: string }
> = {
  parent: {
    bubbleClass: styles.parent,
    label: "👩 Parent",
    alignClass: styles.alignStart,
  },
  tutor: {
    bubbleClass: styles.tutor,
    label: "🎓 Clinical tutor",
    alignClass: styles.alignStart,
  },
  safety: {
    bubbleClass: styles.safety,
    label: "⚠ Safety alert",
    alignClass: styles.alignStart,
  },
  student: {
    bubbleClass: styles.studentBubble,
    label: "You",
    alignClass: styles.alignEnd,
  },
  system: {
    bubbleClass: styles.system,
    label: "",
    alignClass: styles.alignStart,
  },
};

function resolveChatType(type: MessageType): ChatType {
  if (
    type === "parent" ||
    type === "tutor" ||
    type === "safety" ||
    type === "student" ||
    type === "system"
  ) {
    return type;
  }
  return "system";
}

export function MessageBubble({
  type,
  text,
  style,
  className,
}: MessageBubbleProps) {
  if (type === "lab") {
    return <LabResultCard text={text} />;
  }
  if (type === "lab_note") {
    const classes = [styles.labNote, className].filter(Boolean).join(" ");
    return (
      <div className={classes} style={style}>
        {text}
      </div>
    );
  }
  if (type === "lab_tutor") {
    return <TutorCard text={text} style={style} className={className} />;
  }

  const chatType = resolveChatType(type);
  const cfg = CHAT_CONFIG[chatType];
  const rowClasses = [styles.row, cfg.alignClass, className]
    .filter(Boolean)
    .join(" ");
  const bubbleClasses = [
    styles.bubble,
    cfg.bubbleClass,
    chatType === "student" ? styles.student : "",
  ]
    .filter(Boolean)
    .join(" ");
  return (
    <div className={rowClasses} style={style}>
      <div className={bubbleClasses}>
        {cfg.label && <div className={styles.label}>{cfg.label}</div>}
        <div className={styles.body}>{text}</div>
      </div>
    </div>
  );
}
