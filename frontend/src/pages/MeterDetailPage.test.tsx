import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import MeterDetailPage from "./MeterDetailPage";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { useMeterDetail } from "../api/queries/useMeterDetail";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("../api/queries/useMeterDetail");

vi.mock("../api/queries/useRunAnalysis", () => ({
  useRunAnalysis: () => ({ mutate: vi.fn(), isPending: false })
}));

// Mock echarts to avoid canvas rendering issues in jsdom
vi.mock("echarts-for-react", () => ({
  default: () => <div data-testid="mock-echarts" />
}));

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const mockUseMeterDetail = useMeterDetail as any;

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

describe("MeterDetailPage", () => {
  it("renders loading state", () => {
    mockUseMeterDetail.mockReturnValue({ isLoading: true });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/meters/1"]}>
          <Routes>
            <Route path="/meters/:meterId" element={<MeterDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getAllByTestId("skeleton").length).toBeGreaterThan(0);
  });

  it("renders error state", () => {
    mockUseMeterDetail.mockReturnValue({ isError: true });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/meters/1"]}>
          <Routes>
            <Route path="/meters/:meterId" element={<MeterDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getByText("Error al cargar el detalle del medidor.")).toBeInTheDocument();
  });

  it("renders data correctly", () => {
    mockUseMeterDetail.mockReturnValue({
      data: {
        meter_id: "m-1",
        name: "Test Meter",
        location: "Loc",
        status: "ACTIVE",
        consumption_kwh: 100,
        baseline_kwh: 90,
        variation_pct: 11.1,
        readings: [{
          timestamp: "2024-01-01T00:00:00Z",
          consumption_kwh: 10,
          voltage_v: 220,
          current_a: 5,
          power_factor: 0.9,
          status: "ACTIVE"
        }]
      },
      isLoading: false,
      isError: false
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/meters/m-1"]}>
          <Routes>
            <Route path="/meters/:meterId" element={<MeterDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getAllByText("Test Meter")[0]).toBeInTheDocument();
    expect(screen.getByText("Loc")).toBeInTheDocument();
    expect(screen.getByTestId("mock-echarts")).toBeInTheDocument();
  });
});
