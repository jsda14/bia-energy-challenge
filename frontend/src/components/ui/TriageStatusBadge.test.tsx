import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { TriageStatusBadge } from "./TriageStatusBadge";

describe("TriageStatusBadge", () => {
  it("renders 'NEW' status correctly", () => {
    render(<TriageStatusBadge status="NEW" />);
    const badge = screen.getByText("Nueva");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("badge--new");
  });

  it("renders 'ACKNOWLEDGED' status correctly", () => {
    render(<TriageStatusBadge status="ACKNOWLEDGED" />);
    const badge = screen.getByText("Atendida");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("badge--acknowledged");
  });

  it("renders 'DISMISSED' status correctly", () => {
    render(<TriageStatusBadge status="DISMISSED" />);
    const badge = screen.getByText("Descartada");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("badge--dismissed");
  });

  it("renders unknown status gracefully as 'Nueva' fallback", () => {
    render(<TriageStatusBadge status="unknown_status" />);
    const badge = screen.getByText("Nueva");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("badge--new");
  });
});
