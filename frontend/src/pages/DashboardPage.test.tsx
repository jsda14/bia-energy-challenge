import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import DashboardPage from "./DashboardPage";
import { useDashboardSummary } from "../api/queries/useDashboardSummary";
import { useMeters } from "../api/queries/useMeters";
import { useAnomalies } from "../api/queries/useAnomalies";
import { useConsumptionTimeline } from "../api/queries/useConsumptionTimeline";

vi.mock("../api/queries/useDashboardSummary");
vi.mock("../api/queries/useMeters");
vi.mock("../api/queries/useAnomalies");
vi.mock("../api/queries/useConsumptionTimeline");
vi.mock("../api/queries/useRunAnalysis", () => ({
  useRunAnalysis: () => ({ mutate: vi.fn(), isPending: false }),
}));

// Mock echarts to avoid canvas rendering issues in jsdom
vi.mock("echarts-for-react", () => ({
  default: () => <div data-testid="mock-echarts" />,
}));

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const mockUseDashboardSummary = useDashboardSummary as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const mockUseMeters = useMeters as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const mockUseAnomalies = useAnomalies as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const mockUseConsumptionTimeline = useConsumptionTimeline as any;

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

function renderPage() {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const summaryData = {
  anomalies_detected: 3,
  high_priority_count: 1,
  average_confidence: 0.85,
  last_analysis_at: "2026-09-20T00:00:00Z",
};

const metersData = [
  { meter_id: "M-1", name: "Meter 1", status: "OK", consumption_kwh: 100, variation_pct: null, anomaly_severity: null },
];

const anomaliesData = [
  { id: "1", meter_id: "M-1", type: "SPIKE", severity: "HIGH", confidence: 0.9, recommended_action: "Revisar", detected_at: "2026-09-20T00:00:00Z" },
];

const timelineData = { points: [{ timestamp: "2026-09-01T00:00:00Z", total_consumption_kwh: 100 }] };

describe("DashboardPage", () => {
  beforeEach(() => {
    mockUseDashboardSummary.mockReturnValue({ data: summaryData, isLoading: false, isError: false });
    mockUseMeters.mockReturnValue({ data: metersData, isLoading: false, isError: false });
    mockUseAnomalies.mockReturnValue({ data: anomaliesData, isLoading: false, isError: false });
    mockUseConsumptionTimeline.mockReturnValue({ data: timelineData, isLoading: false, isError: false });
  });

  it("renders a loading state while any query is pending", () => {
    mockUseMeters.mockReturnValue({ isLoading: true });
    renderPage();
    expect(screen.getByText("Cargando...")).toBeInTheDocument();
  });

  it("renders an error state when any query fails", () => {
    mockUseAnomalies.mockReturnValue({ isError: true, isLoading: false });
    renderPage();
    expect(screen.getByText("Error al cargar el dashboard.")).toBeInTheDocument();
  });

  it("renders the stat cards and the new SPEC-012 chart sections once loaded", () => {
    renderPage();
    expect(screen.getByText("Anomalías detectadas")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("Alta prioridad")).toBeInTheDocument();
    expect(screen.getByText("Estado de Medidores")).toBeInTheDocument();
    expect(screen.getByText("Triage (Top Anomalías)")).toBeInTheDocument();
    // ConsumptionTimelineChart + MeterStatusDistribution both render mocked echarts
    expect(screen.getAllByTestId("mock-echarts").length).toBe(2);
  });

  it("computes total consumption from meters, not from the backend summary", () => {
    mockUseMeters.mockReturnValue({
      data: [
        { meter_id: "M-1", name: "Meter 1", status: "OK", consumption_kwh: 60, variation_pct: null, anomaly_severity: null },
        { meter_id: "M-2", name: "Meter 2", status: "OK", consumption_kwh: 40, variation_pct: null, anomaly_severity: null },
      ],
      isLoading: false,
      isError: false,
    });
    renderPage();
    expect(screen.getByText("100,0 kWh")).toBeInTheDocument();
  });
});
