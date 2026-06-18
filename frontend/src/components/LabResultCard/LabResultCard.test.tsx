import { render, screen, within } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { LabResultCard } from "./LabResultCard";
import { formatLabText } from "../../lib/labText";
import styles from "./LabResultCard.module.css";

const XLA_IMMUNOGLOBULINS =
  "IgG: <100 mg/dL ↓↓↓ (severely decreased; normal for age >400 mg/dL). IgA: <5 mg/dL (UNDETECTABLE). IgM: <10 mg/dL ↓↓↓ (severely decreased). IgE: <2 IU/mL (absent). Total protein: 42 g/L ↓↓ (low — reflects absent immunoglobulin contribution).";

describe("LabResultCard", () => {
  it("splits a __LAB__ message and renders the uppercase header strip", () => {
    render(<LabResultCard text={formatLabText("immunoglobulins", XLA_IMMUNOGLOBULINS)} />);
    const title = screen.getByText("immunoglobulins");
    expect(title).toHaveClass(styles.title);
    expect(screen.getByText("🔬")).toBeInTheDocument();
  });

  it("renders a table with the IgG row flagged severely-decreased and a ↓↓↓ badge", () => {
    render(<LabResultCard text={formatLabText("immunoglobulins", XLA_IMMUNOGLOBULINS)} />);
    const igg = screen.getByText("IgG");
    const row = igg.closest("tr");
    expect(row).not.toBeNull();
    const valueCell = row!.querySelectorAll("td")[1];
    expect(valueCell).toHaveStyle({ color: "#1A3A8B", fontWeight: 600 });
    expect(within(valueCell as HTMLElement).getByText("↓↓↓")).toBeInTheDocument();
  });

  it("flags IgA as ABSENT (undetectable) within its row", () => {
    render(<LabResultCard text={formatLabText("immunoglobulins", XLA_IMMUNOGLOBULINS)} />);
    const row = screen.getByText("IgA").closest("tr");
    expect(row).not.toBeNull();
    const valueCell = row!.querySelectorAll("td")[1];
    expect(within(valueCell as HTMLElement).getByText("ABSENT")).toBeInTheDocument();
  });

  it("accepts an explicit header plus body text", () => {
    render(
      <LabResultCard header="immunoglobulins" text={XLA_IMMUNOGLOBULINS} />,
    );
    expect(screen.getByText("immunoglobulins")).toHaveClass(styles.title);
    expect(screen.getByText("IgG")).toBeInTheDocument();
  });

  it("renders a plain text block when the body has no parsable rows", () => {
    render(
      <LabResultCard
        text={formatLabText("clinical note", "NOTE: Discuss findings with the immunology team")}
      />,
    );
    expect(screen.queryByRole("table")).toBeNull();
    expect(
      screen.getByText("Discuss findings with the immunology team"),
    ).toHaveClass(styles.textLine);
  });
});
