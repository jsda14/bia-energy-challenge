import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { MobileNav } from "./MobileNav";

const items = [
  { label: "Dashboard", to: "/" },
  { label: "Medidores", to: "/meters" },
  { label: "Anomalías", to: "/anomalies" },
];

describe("MobileNav", () => {
  it("renders all provided links", () => {
    render(
      <MemoryRouter>
        <MobileNav items={items} onClose={vi.fn()} />
      </MemoryRouter>
    );
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Medidores")).toBeInTheDocument();
    expect(screen.getByText("Anomalías")).toBeInTheDocument();
  });

  it("calls onClose when a link is clicked", () => {
    const onClose = vi.fn();
    render(
      <MemoryRouter>
        <MobileNav items={items} onClose={onClose} />
      </MemoryRouter>
    );
    fireEvent.click(screen.getByText("Medidores"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when Escape is pressed", () => {
    const onClose = vi.fn();
    render(
      <MemoryRouter>
        <MobileNav items={items} onClose={onClose} />
      </MemoryRouter>
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
