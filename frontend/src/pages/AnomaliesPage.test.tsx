import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import AnomaliesPage from "./AnomaliesPage";
import { useAnomalies } from "../api/queries/useAnomalies";
import { MemoryRouter } from "react-router-dom";

vi.mock("../api/queries/useAnomalies");
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const mockUseAnomalies = useAnomalies as any;

describe("AnomaliesPage", () => {
  it("renders loading state", () => {
    mockUseAnomalies.mockReturnValue({ isLoading: true });
    render(<AnomaliesPage />);
    expect(screen.getByText("Cargando...")).toBeInTheDocument();
  });

  it("renders error state", () => {
    mockUseAnomalies.mockReturnValue({ isError: true });
    render(<AnomaliesPage />);
    expect(screen.getByText("Error al cargar la lista de anomalías.")).toBeInTheDocument();
  });

  it("renders empty state", () => {
    mockUseAnomalies.mockReturnValue({ data: [] });
    render(<AnomaliesPage />);
    expect(screen.getByText("No hay anomalías detectadas.")).toBeInTheDocument();
  });

  it("renders data correctly", () => {
    mockUseAnomalies.mockReturnValue({
      data: [{
        id: "1",
        meter_id: "m-1",
        type: "T",
        severity: "HIGH",
        confidence: 0.9,
        recommended_action: "R",
        detected_at: "2024-01-01T00:00:00Z"
      }],
      isLoading: false,
      isError: false
    });
    render(
      <MemoryRouter>
        <AnomaliesPage />
      </MemoryRouter>
    );
    expect(screen.getByText("Anomalías")).toBeInTheDocument();
    expect(screen.getByText("m-1")).toBeInTheDocument();
  });
});
