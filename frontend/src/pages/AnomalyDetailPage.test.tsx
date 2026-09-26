import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AnomalyDetailPage from "./AnomalyDetailPage";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { useAnomalyDetail } from "../api/queries/useAnomalyDetail";
import { useMeterDetail } from "../api/queries/useMeterDetail";
import { useRegenerateExplanation } from "../api/queries/useRegenerateExplanation";

vi.mock("../api/queries/useAnomalyDetail");
vi.mock("../api/queries/useMeterDetail");
vi.mock("../api/queries/useRegenerateExplanation");
vi.mock("../api/queries/useRegenerateExplanation");

// RunAnalysisButton (agregado en el detalle de anomalía) usa useRunAnalysis
// internamente — se mockea igual que en MeterDetailPage.test.tsx.
vi.mock("../api/queries/useRunAnalysis", () => ({
  useRunAnalysis: () => ({ mutate: vi.fn(), isPending: false })
}));

// Mock echarts to avoid canvas rendering issues in jsdom
vi.mock("echarts-for-react", () => ({
  default: () => <div data-testid="mock-echarts" />
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const mockUseAnomalyDetail = useAnomalyDetail as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const mockUseMeterDetail = useMeterDetail as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const mockUseRegenerateExplanation = useRegenerateExplanation as any;

describe("AnomalyDetailPage", () => {
  beforeEach(() => {
    mockUseRegenerateExplanation.mockReturnValue({ mutate: vi.fn(), isPending: false, isError: false });
  });

  it("renders loading state", () => {
    mockUseAnomalyDetail.mockReturnValue({ isLoading: true });
    mockUseMeterDetail.mockReturnValue({ isLoading: false });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/anomalies/1"]}>
          <Routes>
            <Route path="/anomalies/:id" element={<AnomalyDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getByText("Cargando...")).toBeInTheDocument();
  });

  it("renders error state", () => {
    mockUseAnomalyDetail.mockReturnValue({ isError: true });
    mockUseMeterDetail.mockReturnValue({ isLoading: false });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/anomalies/1"]}>
          <Routes>
            <Route path="/anomalies/:id" element={<AnomalyDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
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
        window_end: "2024-01-01T01:00:00Z",
        explanation_source: "ai"
      },
      isLoading: false,
      isError: false
    });

    mockUseMeterDetail.mockReturnValue({
      data: {
        readings: [{
          timestamp: "2024-01-01T00:00:00Z",
          consumption_kwh: 10,
          voltage_v: 220,
          current_a: 5,
          power_factor: 0.9,
          status: "ACTIVE"
        }],
        baseline_kwh: 100
      },
      isLoading: false,
      isError: false
    });
    
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/anomalies/1"]}>
          <Routes>
            <Route path="/anomalies/:id" element={<AnomalyDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText("meter-123")).toBeInTheDocument();
    expect(screen.getByText("Test reason")).toBeInTheDocument();
    expect(screen.getByText("Sin evento correlacionado")).toBeInTheDocument();
    expect(screen.getByText("+78,9%")).toBeInTheDocument();
    // Test CB-03: empty affected variables shows "Ninguna"
    expect(screen.getByText("Ninguna")).toBeInTheDocument();
    // Test that visual evidence chart is rendered
    expect(screen.getByTestId("mock-echarts")).toBeInTheDocument();
  });

  it("renders error for visual evidence independently", () => {
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
        window_end: "2024-01-01T01:00:00Z",
        explanation_source: "ai"
      },
      isLoading: false,
      isError: false
    });

    mockUseMeterDetail.mockReturnValue({
      isError: true,
      isLoading: false
    });
    
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/anomalies/1"]}>
          <Routes>
            <Route path="/anomalies/:id" element={<AnomalyDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText("Test reason")).toBeInTheDocument();
    expect(screen.getByText("Error al cargar la evidencia visual.")).toBeInTheDocument();
  });

  it("handles regenerate explanation button click, loading and error states", async () => {
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
        window_end: "2024-01-01T01:00:00Z",
        explanation_source: "ai"
      },
      isLoading: false,
      isError: false
    });

    mockUseMeterDetail.mockReturnValue({
      data: { readings: [], baseline_kwh: 100 },
      isLoading: false,
      isError: false
    });

    const mutateMock = vi.fn();
    mockUseRegenerateExplanation.mockReturnValue({ mutate: mutateMock, isPending: false, isError: false });

    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/anomalies/1"]}>
          <Routes>
            <Route path="/anomalies/:id" element={<AnomalyDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    const btn = screen.getByText("Regenerar explicación con IA");
    expect(btn).toBeInTheDocument();
    
    // Test click
    btn.click();
    expect(mutateMock).toHaveBeenCalledWith("1");

    // Test loading
    mockUseRegenerateExplanation.mockReturnValue({ mutate: mutateMock, isPending: true, isError: false });
    rerender(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/anomalies/1"]}>
          <Routes>
            <Route path="/anomalies/:id" element={<AnomalyDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getAllByText("La IA está analizando…").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "La IA está analizando…" })).toBeDisabled();

    // Test error
    mockUseRegenerateExplanation.mockReturnValue({ mutate: mutateMock, isPending: false, isError: true });
    rerender(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/anomalies/1"]}>
          <Routes>
            <Route path="/anomalies/:id" element={<AnomalyDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getByText("Error al regenerar la explicación.")).toBeInTheDocument();
  });
});
