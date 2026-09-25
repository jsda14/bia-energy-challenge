import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import AnomalyDetailPage from "./AnomalyDetailPage";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { useAnomalyDetail } from "../api/queries/useAnomalyDetail";

vi.mock("../api/queries/useAnomalyDetail");
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const mockUseAnomalyDetail = useAnomalyDetail as any;

describe("AnomalyDetailPage", () => {
  it("renders loading state", () => {
    mockUseAnomalyDetail.mockReturnValue({ isLoading: true });
    render(
      <MemoryRouter initialEntries={["/anomalies/1"]}>
        <Routes>
          <Route path="/anomalies/:id" element={<AnomalyDetailPage />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText("Cargando...")).toBeInTheDocument();
  });

  it("renders error state", () => {
    mockUseAnomalyDetail.mockReturnValue({ isError: true });
    render(
      <MemoryRouter initialEntries={["/anomalies/1"]}>
        <Routes>
          <Route path="/anomalies/:id" element={<AnomalyDetailPage />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText("Error al cargar el detalle de la anomalía.")).toBeInTheDocument();
  });

  it("renders data correctly and handles empty affected variables", () => {
    mockUseAnomalyDetail.mockReturnValue({
      data: {
        id: "1",
        meter_id: "meter-123",
        type: "SPIKE",
        severity: "HIGH",
        confidence: 0.99,
        reason: "Test reason",
        recommended_action: "Test action",
        baseline_kwh: 100,
        observed_kwh: 200,
        variation_pct: 78.9,
        affected_variables: [],
        correlated_event: null,
        window_start: "2024-01-01T00:00:00Z",
        window_end: "2024-01-01T01:00:00Z"
      },
      isLoading: false,
      isError: false
    });
    
    render(
      <MemoryRouter initialEntries={["/anomalies/1"]}>
        <Routes>
          <Route path="/anomalies/:id" element={<AnomalyDetailPage />} />
        </Routes>
      </MemoryRouter>
    );
    
    expect(screen.getByText("meter-123")).toBeInTheDocument();
    expect(screen.getByText("Test reason")).toBeInTheDocument();
    expect(screen.getByText("Sin evento correlacionado")).toBeInTheDocument();
    expect(screen.getByText("+78,9%")).toBeInTheDocument();
    // Test CB-03: empty affected variables shows "—"
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
