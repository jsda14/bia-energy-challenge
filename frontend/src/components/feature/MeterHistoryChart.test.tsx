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

  it("renders chart and NO variable chips by default", () => {
    render(<MeterHistoryChart readings={mockReadings} baselineKwh={10} />);
    expect(screen.getByTestId("mock-echarts")).toBeInTheDocument();
    expect(screen.queryByTestId("chip-voltage_v")).not.toBeInTheDocument();
  });

  it("shows variable chips when compare mode is enabled, allows selecting multiple at once, and prevents deselecting the last one", async () => {
    const user = userEvent.setup();
    render(<MeterHistoryChart readings={mockReadings} baselineKwh={10} />);

    const toggle = screen.getByTestId("toggle-compare");
    await user.click(toggle);

    const voltageChip = screen.getByTestId("chip-voltage_v");
    const currentChip = screen.getByTestId("chip-current_a");
    const powerFactorChip = screen.getByTestId("chip-power_factor");
    expect(voltageChip).toBeInTheDocument();

    // voltage_v selected by default when entering compare mode.
    expect(voltageChip).toHaveAttribute("aria-pressed", "true");
    expect(currentChip).toHaveAttribute("aria-pressed", "false");

    // Clicking additional chips ADDS them — no modifier key required,
    // several variables can be active at once (this is the real bug
    // being fixed: a native <select multiple> required Ctrl/Cmd+click,
    // wasn't discoverable, and the user reported it behaving like a
    // single-select in practice).
    await user.click(currentChip);
    await user.click(powerFactorChip);
    expect(voltageChip).toHaveAttribute("aria-pressed", "true");
    expect(currentChip).toHaveAttribute("aria-pressed", "true");
    expect(powerFactorChip).toHaveAttribute("aria-pressed", "true");

    // RN-02: deselecting down to the last one is blocked.
    await user.click(voltageChip);
    await user.click(currentChip);
    expect(powerFactorChip).toHaveAttribute("aria-pressed", "true");
    await user.click(powerFactorChip);
    expect(powerFactorChip).toHaveAttribute("aria-pressed", "true"); // still selected, click ignored
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
