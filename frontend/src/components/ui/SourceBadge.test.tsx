import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { SourceBadge } from "./SourceBadge";

describe("SourceBadge", () => {
  it("renders 'ai' source correctly", () => {
    render(<SourceBadge source="ai" />);
    const badge = screen.getByText("Generado por IA");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("badge--ai");
  });

  it("renders 'template' source correctly", () => {
    render(<SourceBadge source="template" />);
    const badge = screen.getByText("Plantilla predefinida");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("badge--template");
  });

  it("renders unknown source gracefully as template fallback", () => {
    render(<SourceBadge source="unknown_source" />);
    const badge = screen.getByText("Plantilla predefinida");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("badge--template");
  });
});
