import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { LabTable } from "./LabTable";
import { parseLabText } from "../../lib/labText";
import styles from "./LabTable.module.css";

describe("LabTable", () => {
  it("renders Parameter and Result column headers", () => {
    render(<LabTable rows={parseLabText("IgG: <100 mg/dL ↓↓↓")} />);
    expect(screen.getByText("Parameter")).toHaveClass(styles.th);
    expect(screen.getByText("Result")).toHaveClass(styles.th);
  });

  it("flags a severely decreased value with the lo3 badge and value text colour", () => {
    render(<LabTable rows={parseLabText("IgG: <100 mg/dL ↓↓↓ (severely decreased)")} />);
    const param = screen.getByText("IgG");
    expect(param).toHaveClass(styles.paramCell);
    const valueCell = param.closest("tr")?.querySelectorAll("td")[1];
    expect(valueCell).toHaveStyle({ color: "#1A3A8B", fontWeight: 600 });
    expect(screen.getByText("↓↓↓")).toBeInTheDocument();
  });

  it("zebra-stripes neutral rows using the all-rows index", () => {
    const rows = parseLabText("Alpha: 12 things. Beta: 34 things.");
    render(<LabTable rows={rows} />);
    const alphaRow = screen.getByText("Alpha").closest("tr");
    const betaRow = screen.getByText("Beta").closest("tr");
    expect(alphaRow).toHaveStyle({ background: "#ffffff" });
    expect(betaRow).toHaveStyle({ background: "#F8FAFC" });
  });
});
