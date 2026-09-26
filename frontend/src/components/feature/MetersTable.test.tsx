import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { MetersTable } from "./MetersTable";
import type { MeterSummary } from "../../domain/types";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

function makeMeter(overrides: Partial<MeterSummary>): MeterSummary {
  return {
    meter_id: "M-1",
    name: "Meter 1",
    status: "OK",
    consumption_kwh: 100,
    variation_pct: null,
    anomaly_severity: null,
    ...overrides,
  };
}

describe("MetersTable", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  it("renders the empty state when there are no meters", () => {
    render(
      <MemoryRouter>
        <MetersTable meters={[]} />
      </MemoryRouter>
    );
    expect(screen.getByText("Sin resultados para el filtro seleccionado.")).toBeInTheDocument();
  });

  it("renders neutral variation for values within norm (RN-06 <30%)", () => {
    render(
      <MemoryRouter>
        <MetersTable meters={[makeMeter({ variation_pct: 10 })]} />
      </MemoryRouter>
    );
    expect(screen.getByText("Dentro de norma")).toBeInTheDocument();
  });

  it("renders a warning badge with an up arrow for 30-80% variation", () => {
    render(
      <MemoryRouter>
        <MetersTable meters={[makeMeter({ variation_pct: 45 })]} />
      </MemoryRouter>
    );
    expect(screen.getByText("▲ +45,0%")).toBeInTheDocument();
  });

  it("renders a critical badge with a down arrow for >=80% variation", () => {
    render(
      <MemoryRouter>
        <MetersTable meters={[makeMeter({ variation_pct: -85 })]} />
      </MemoryRouter>
    );
    expect(screen.getByText("▼ +85,0%")).toBeInTheDocument();
  });

  it("renders a dash when variation_pct is null", () => {
    render(
      <MemoryRouter>
        <MetersTable meters={[makeMeter({ variation_pct: null })]} />
      </MemoryRouter>
    );
    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBeGreaterThan(0);
  });

  it("sorts by column on header click, cycling asc -> desc -> unsorted", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <MetersTable
          meters={[
            makeMeter({ meter_id: "M-1", name: "B Meter", consumption_kwh: 50 }),
            makeMeter({ meter_id: "M-2", name: "A Meter", consumption_kwh: 100 }),
          ]}
        />
      </MemoryRouter>
    );

    const nameHeader = screen.getByText("Nombre");
    await user.click(nameHeader);
    let cells = screen.getAllByText(/Meter$/);
    expect(cells[0]).toHaveTextContent("A Meter");

    await user.click(screen.getByText(/Nombre/));
    cells = screen.getAllByText(/Meter$/);
    expect(cells[0]).toHaveTextContent("B Meter");
  });

  it("navigates to the meter detail page on row click", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <MetersTable meters={[makeMeter({ meter_id: "M-42" })]} />
      </MemoryRouter>
    );
    await user.click(screen.getByRole("button", { name: /Meter 1/ }));
    expect(mockNavigate).toHaveBeenCalledWith("/meters/M-42");
  });
});
