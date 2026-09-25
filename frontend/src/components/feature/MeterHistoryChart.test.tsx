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

  it("renders chart and NO select by default", () => {
    render(<MeterHistoryChart readings={mockReadings} baselineKwh={10} />);
    expect(screen.getByTestId("mock-echarts")).toBeInTheDocument();
    expect(screen.queryByTestId("select-multi-series")).not.toBeInTheDocument();
  });

  it("shows multi-select when compare mode is enabled and prevents unselecting last variable", async () => {
    const user = userEvent.setup();
    render(<MeterHistoryChart readings={mockReadings} baselineKwh={10} />);
    
    const toggle = screen.getByTestId("toggle-compare");
    await user.click(toggle);

    const multiSelect = screen.getByTestId("select-multi-series");
    expect(multiSelect).toBeInTheDocument();

    // Deselect voltage_v to test fallback
    await user.deselectOptions(multiSelect, "voltage_v");
    // RN-02: Should fallback to voltage_v if empty
    expect((multiSelect as HTMLSelectElement).selectedOptions[0].value).toBe("voltage_v");
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
