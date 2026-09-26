import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Skeleton } from "./Skeleton";

describe("Skeleton", () => {
  it("renders without throwing, with default dimensions", () => {
    render(<Skeleton />);
    const el = screen.getByTestId("skeleton");
    expect(el).toBeInTheDocument();
    expect(el).toHaveStyle({ width: "100%", height: "1rem" });
  });

  it("applies custom width/height passed via props", () => {
    render(<Skeleton width="40px" height="120px" />);
    const el = screen.getByTestId("skeleton");
    expect(el).toHaveStyle({ width: "40px", height: "120px" });
  });

  it("is hidden from assistive tech (aria-hidden)", () => {
    render(<Skeleton />);
    expect(screen.getByTestId("skeleton")).toHaveAttribute("aria-hidden", "true");
  });
});
