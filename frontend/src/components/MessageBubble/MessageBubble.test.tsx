import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MessageBubble } from "./MessageBubble";
import styles from "./MessageBubble.module.css";
import tutorStyles from "../TutorCard/TutorCard.module.css";
import labStyles from "../LabResultCard/LabResultCard.module.css";

describe("MessageBubble — chat bubble types", () => {
  it("renders the parent bubble with label and pre-wrap body, aligned start", () => {
    const { container } = render(
      <MessageBubble type="parent" text="He has had pneumonia twice." />,
    );
    const row = container.firstChild as HTMLElement;
    expect(row).toHaveClass(styles.row);
    expect(row).toHaveClass(styles.alignStart);
    const bubble = row.firstChild as HTMLElement;
    expect(bubble).toHaveClass(styles.bubble);
    expect(bubble).toHaveClass(styles.parent);
    expect(bubble).not.toHaveClass(styles.student);
    expect(screen.getByText("👩 Parent")).toHaveClass(styles.label);
    expect(screen.getByText("He has had pneumonia twice.")).toHaveClass(
      styles.body,
    );
  });

  it("renders the student bubble aligned end with the asymmetric student radius", () => {
    const { container } = render(<MessageBubble type="student" text="Hello" />);
    const row = container.firstChild as HTMLElement;
    expect(row).toHaveClass(styles.alignEnd);
    const bubble = row.firstChild as HTMLElement;
    expect(bubble).toHaveClass(styles.studentBubble);
    expect(bubble).toHaveClass(styles.student);
    expect(screen.getByText("You")).toHaveClass(styles.label);
  });

  it("renders the tutor and safety labels", () => {
    render(<MessageBubble type="tutor" text="Compare X and Y." />);
    expect(screen.getByText("🎓 Clinical tutor")).toBeInTheDocument();
    render(<MessageBubble type="safety" text="Safety alert" />);
    expect(screen.getByText("⚠ Safety alert")).toBeInTheDocument();
  });

  it("renders the system bubble without a label", () => {
    const { container } = render(
      <MessageBubble type="system" text="Investigations updated." />,
    );
    const bubble = container.querySelector(`.${styles.system}`) as HTMLElement;
    expect(bubble).toBeInTheDocument();
    expect(bubble.querySelector(`.${styles.label}`)).toBeNull();
    expect(screen.getByText("Investigations updated.")).toHaveClass(
      styles.body,
    );
  });

  it("falls back to the system config for an unknown type", () => {
    const { container } = render(
      <MessageBubble
        type={"weird" as unknown as "system"}
        text="fallback body"
      />,
    );
    const bubble = container.querySelector(`.${styles.system}`) as HTMLElement;
    expect(bubble).toBeInTheDocument();
    expect(bubble.querySelector(`.${styles.label}`)).toBeNull();
  });
});

describe("MessageBubble — investigations types", () => {
  it("renders lab_note as a plain surfaceAlt box", () => {
    const { container } = render(
      <MessageBubble type="lab_note" text="Results not yet available." />,
    );
    const box = container.firstChild as HTMLElement;
    expect(box).toHaveClass(styles.labNote);
    expect(box).toHaveTextContent("Results not yet available.");
  });

  it("delegates lab_tutor to the TutorCard", () => {
    const { container } = render(
      <MessageBubble type="lab_tutor" text="Think about the compartment." />,
    );
    const card = container.firstChild as HTMLElement;
    expect(card).toHaveClass(tutorStyles.card);
    expect(screen.getByText("🎓 Clinical tutor")).toHaveClass(
      tutorStyles.label,
    );
    expect(screen.getByText("Think about the compartment.")).toHaveClass(
      tutorStyles.body,
    );
  });

  it("delegates lab to the LabResultCard with the header and rows", () => {
    const text = "__LAB__Immunoglobulins\nIgG: 0.8 g/L ↓↓";
    render(<MessageBubble type="lab" text={text} />);
    expect(screen.getByText("Immunoglobulins")).toHaveClass(labStyles.title);
    expect(screen.getByText("Parameter")).toBeInTheDocument();
    expect(screen.getByText("Result")).toBeInTheDocument();
    expect(screen.getByText("IgG")).toBeInTheDocument();
  });
});
