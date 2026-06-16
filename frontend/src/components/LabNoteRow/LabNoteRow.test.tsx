import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { LabNoteRow } from "./LabNoteRow";
import styles from "./LabNoteRow.module.css";

function renderInTable(text: string) {
  return render(
    <table>
      <tbody>
        <LabNoteRow text={text} />
      </tbody>
    </table>,
  );
}

describe("LabNoteRow", () => {
  it("renders the warning glyph and note text in a full-width amber cell", () => {
    renderInTable("Discuss with immunology before transfusion.");
    const cell = screen.getByText(/Discuss with immunology before transfusion\./);
    expect(cell.tagName).toBe("TD");
    expect(cell).toHaveAttribute("colspan", "2");
    expect(cell).toHaveClass(styles.cell);
    expect(cell.textContent).toBe("⚠ Discuss with immunology before transfusion.");
  });

  it("places the amber background on the row", () => {
    renderInTable("note");
    const cell = screen.getByText(/note/);
    expect(cell.parentElement).toHaveClass(styles.row);
  });
});
