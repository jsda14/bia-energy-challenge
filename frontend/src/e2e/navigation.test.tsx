import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { router } from "../router";
import { apiClient } from "../api/client";

// Mock API Client
vi.mock("../api/client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// Mock echarts to avoid canvas rendering issues in jsdom
vi.mock("echarts-for-react", () => ({
  default: () => <div data-testid="mock-echarts" />
}));

import type { Mock } from "vitest";

const mockApiClient = apiClient as unknown as { get: Mock; post: Mock };

const MOCK_ANOMALIES = [
  { 
    id: "a-123", 
    meter_id: "meter-123", 
    type: "SPIKE", 
    severity: "HIGH", 
    confidence: 0.99, 
    recommended_action: "Check",
    detected_at: "2024-01-01T00:00:00Z" 
  }
];

const MOCK_METERS = [
  { 
    meter_id: "meter-123", 
    name: "Mock Meter", 
    status: "ACTIVE", 
    consumption_kwh: 100,
    variation_pct: 11.1,
    anomaly_severity: "HIGH"
  }
];

const MOCK_DASHBOARD = {
  anomalies_detected: 1,
  high_priority_count: 1,
  average_confidence: 0.99,
  last_analysis_at: "2024-01-01T00:00:00Z"
};

const MOCK_METER_DETAIL = {
  meter_id: "meter-123",
  name: "Mock Meter",
  location: "Loc",
  status: "ACTIVE",
  consumption_kwh: 100,
  baseline_kwh: 90,
  variation_pct: 11.1,
  readings: []
};

const MOCK_ANOMALY_DETAIL = {
  ...MOCK_ANOMALIES[0],
  reason: "Spike detected",
  recommended_action: "Check",
  baseline_kwh: 100,
  observed_kwh: 200,
  variation_pct: 100.0,
  affected_variables: [],
  correlated_event: null,
  window_start: "2024-01-01T00:00:00Z",
  window_end: "2024-01-01T01:00:00Z",
  explanation_source: "ai"
};

describe("E2E Navigation", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          gcTime: 0 as any,
        },
      },
    });

    mockApiClient.get.mockImplementation(async (endpoint: string) => {
      if (endpoint === "/dashboard/summary") return MOCK_DASHBOARD;
      if (endpoint === "/meters") return MOCK_METERS;
      if (endpoint === "/meters/meter-123") return MOCK_METER_DETAIL;
      if (endpoint === "/anomalies") return MOCK_ANOMALIES;
      if (endpoint === "/anomalies/a-123") return MOCK_ANOMALY_DETAIL;
      return null;
    });
  });

  const renderApp = (initialEntries = ["/"]) => {
    const memoryRouter = createMemoryRouter(router.routes, { initialEntries });
    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={memoryRouter} />
      </QueryClientProvider>
    );
    return memoryRouter;
  };

  it("navigates from Dashboard to MeterListPage", async () => {
    const user = userEvent.setup();
    renderApp(["/"]);

    // Wait for Dashboard to load
    await waitFor(() => {
      expect(screen.getByText("Bia Energy")).toBeInTheDocument(); // Header title
      expect(screen.getAllByText("1")[0]).toBeInTheDocument(); // Active anomalies count
    });

    // Click "Medidores" link in Header
    const metersLink = screen.getByRole("link", { name: "Medidores" });
    await user.click(metersLink);

    // Verify we are on MeterListPage
    await waitFor(() => {
      // The table should have the meter row
      expect(screen.getByText("Mock Meter")).toBeInTheDocument();
    });
  });

  it("navigates from MeterListPage to MeterDetailPage", async () => {
    const user = userEvent.setup();
    renderApp(["/meters"]);

    await waitFor(() => {
      expect(screen.getByText("Mock Meter")).toBeInTheDocument();
    });

    const row = screen.getByText("Mock Meter");
    await user.click(row);

    // Verify MeterDetailPage
    await waitFor(() => {
      expect(screen.getByText("Detalle de Medidor")).toBeInTheDocument();
      expect(screen.getByText("Historial de Lecturas")).toBeInTheDocument();
    });
  });

  it("navigates from Header to AnomaliesPage and then to AnomalyDetailPage", async () => {
    const user = userEvent.setup();
    renderApp(["/"]);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText("Bia Energy")).toBeInTheDocument();
    });

    // Click "Anomalías" link
    const anomaliesLink = screen.getByRole("link", { name: "Anomalías" });
    await user.click(anomaliesLink);

    // Verify AnomaliesPage
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Anomalías" })).toBeInTheDocument();
      expect(screen.getByTestId("anomaly-row-a-123")).toBeInTheDocument();
    });

    const row = screen.getByTestId("anomaly-row-a-123");
    await user.click(row);

    // Verify AnomalyDetailPage
    await waitFor(() => {
      expect(screen.getByText("Detalle de Anomalía")).toBeInTheDocument();
      expect(screen.getByText("Evidencia Visual")).toBeInTheDocument();
      expect(screen.getByText("Spike detected")).toBeInTheDocument();
    });
  });
});
