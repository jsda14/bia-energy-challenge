import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { AnomaliesTable } from "./AnomaliesTable";
import { MemoryRouter } from "react-router-dom";
import type { AnomalySummary } from "../../domain/types";

const mockAnomalies: AnomalySummary[] = [
  {
    id: "anom-1",
    meter_id: "meter-1",
    type: "SPIKE",
    severity: "HIGH",
    confidence: 0.95,
    recommended_action: "Check",
    detected_at: "2024-01-01T10:00:00Z"
  }
];

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("AnomaliesTable", () => {
  it("renders correctly", () => {
    render(
      <MemoryRouter>
        <AnomaliesTable anomalies={mockAnomalies} />
      </MemoryRouter>
    );
    expect(screen.getByText("meter-1")).toBeInTheDocument();
    expect(screen.getByText("SPIKE")).toBeInTheDocument();
  });

  it("navigates on row click", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <AnomaliesTable anomalies={mockAnomalies} />
      </MemoryRouter>
    );

    const row = screen.getByTestId("anomaly-row-anom-1");
    await user.click(row);

    expect(mockNavigate).toHaveBeenCalledWith("/anomalies/anom-1");
  });

  it("navigates on enter key", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <AnomaliesTable anomalies={mockAnomalies} />
      </MemoryRouter>
    );

    const row = screen.getByTestId("anomaly-row-anom-1");
    row.focus();
    await user.keyboard("{Enter}");

    expect(mockNavigate).toHaveBeenCalledWith("/anomalies/anom-1");
  });
});
