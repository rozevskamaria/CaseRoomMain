import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { TabBar } from "./TabBar";
import styles from "./TabBar.module.css";

const tabs = [
  { key: "consultation", label: "💬 Consultation" },
  { key: "investigations", label: "🔬 Investigations", badge: 3 },
  { key: "diagnosis", label: "📋 Final Diagnosis" },
];

describe("TabBar", () => {
  it("renders all tab labels", () => {
    render(<TabBar tabs={tabs} active="consultation" onChange={() => {}} />);
    expect(screen.getByRole("button", { name: /Consultation/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Investigations/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Final Diagnosis/ })).toBeInTheDocument();
  });

  it("marks only the active tab with the active class", () => {
    render(<TabBar tabs={tabs} active="investigations" onChange={() => {}} />);
    expect(screen.getByRole("button", { name: /Consultation/ })).not.toHaveClass(styles.active);
    expect(screen.getByRole("button", { name: /Investigations/ })).toHaveClass(styles.active);
    expect(screen.getByRole("button", { name: /Diagnosis/ })).not.toHaveClass(styles.active);
  });

  it("renders a count badge only when badge > 0", () => {
    render(<TabBar tabs={tabs} active="consultation" onChange={() => {}} />);
    const badged = screen.getByRole("button", { name: /Investigations/ });
    const badge = badged.querySelector(`.${styles.badge}`);
    expect(badge).not.toBeNull();
    expect(badge).toHaveTextContent("3");
    const plain = screen.getByRole("button", { name: /Consultation/ });
    expect(plain.querySelector(`.${styles.badge}`)).toBeNull();
  });

  it("does not render a badge when badge is 0", () => {
    render(
      <TabBar
        tabs={[{ key: "investigations", label: "🔬 Investigations", badge: 0 }]}
        active="investigations"
        onChange={() => {}}
      />,
    );
    expect(screen.getByRole("button").querySelector(`.${styles.badge}`)).toBeNull();
  });

  it("calls onChange with the tab key on click", () => {
    const onChange = vi.fn();
    render(<TabBar tabs={tabs} active="consultation" onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: /Diagnosis/ }));
    expect(onChange).toHaveBeenCalledWith("diagnosis");
  });

  it("applies the container class and style overrides", () => {
    const { container } = render(
      <TabBar tabs={tabs} active="consultation" onChange={() => {}} style={{ opacity: 0.5 }} />,
    );
    const root = container.firstChild as HTMLElement;
    expect(root).toHaveClass(styles.tabBar);
    expect(root).toHaveStyle({ opacity: "0.5" });
  });
});
