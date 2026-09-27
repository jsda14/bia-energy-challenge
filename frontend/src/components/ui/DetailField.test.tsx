import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { DetailField } from "./DetailField";

describe("DetailField", () => {
  it("renders label and value correctly", () => {
    render(<DetailField label="Test Label" value="Test Value" />);
    
    expect(screen.getByText("Test Label")).toBeInTheDocument();
    expect(screen.getByText("Test Value")).toBeInTheDocument();
  });

  it("applies tone class when provided", () => {
    const { container } = render(<DetailField label="T" value="V" tone="critical" />);
    // Check if the appropriate CSS module class modifier is applied
    expect(container.firstChild).toHaveClass(/detail-field--critical/);
  });
});
