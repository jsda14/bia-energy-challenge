import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { MeterHistoryChart } from "./MeterHistoryChart";
import type { Reading } from "../../domain/types";

// Mock echarts to avoid canvas rendering issues in jsdom
vi.mock("echarts-for-react", () => ({
  default: () => <div data-testid="mock-echarts" />
}));

const mockReadings: Reading[] = [
  {
    timestamp: "2024-01-01T00:00:00Z",
    consumption_kwh: 10,
    voltage_v: 220,
    current_a: 5,
    power_factor: 0.9,
    status: "ACTIVE"
  }
];

describe("MeterHistoryChart", () => {
  it("renders empty state when no readings provided", () => {
    render(<MeterHistoryChart readings={[]} baselineKwh={10} />);
    expect(screen.getByText("Sin datos históricos para este medidor.")).toBeInTheDocument();
  });

  it("renders chart and single series controls by default", () => {
    render(<MeterHistoryChart readings={mockReadings} baselineKwh={10} />);
    expect(screen.getByTestId("mock-echarts")).toBeInTheDocument();
    expect(screen.getByTestId("select-series-a")).toBeInTheDocument();
    expect(screen.queryByTestId("select-series-b")).not.toBeInTheDocument();
  });

  it("shows second series select when compare toggle is activated", async () => {
    const user = userEvent.setup();
    render(<MeterHistoryChart readings={mockReadings} baselineKwh={10} />);
    
    const toggle = screen.getByTestId("toggle-compare");
    await user.click(toggle);
    
    expect(screen.getByTestId("select-series-b")).toBeInTheDocument();
  });

  it("renders with highlight correctly without crashing", () => {
    render(
      <MeterHistoryChart 
        readings={mockReadings} 
        baselineKwh={10} 
        highlightStart="2024-01-01T00:00:00Z" 
        highlightEnd="2024-01-01T01:00:00Z" 
      />
    );
    expect(screen.getByTestId("mock-echarts")).toBeInTheDocument();
  });
});
