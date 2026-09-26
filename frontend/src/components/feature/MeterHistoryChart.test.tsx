import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { MeterHistoryChart } from "./MeterHistoryChart";
import type { Reading, Event } from "../../domain/types";

// Mock echarts to avoid canvas rendering issues in jsdom
vi.mock("echarts-for-react", () => ({
  default: (props: { option: unknown }) => (
    <div data-testid="mock-echarts" data-option={JSON.stringify(props.option)} />
  ),
}));

const readings: Reading[] = [
  { timestamp: "2026-09-01T00:00:00Z", consumption_kwh: 10, voltage_v: 220, current_a: 5, power_factor: 0.9, status: "ACTIVE" },
  { timestamp: "2026-09-01T01:00:00Z", consumption_kwh: 15, voltage_v: 221, current_a: 6, power_factor: 0.91, status: "ACTIVE" },
];

const events: Event[] = [
  { event_timestamp: "2026-09-01T00:30:00Z", event_type: "OPERATIONAL_CHANGE", description: "New line" },
];

describe("MeterHistoryChart", () => {
  it("renders the empty state when there are no readings", () => {
    render(<MeterHistoryChart readings={[]} baselineKwh={null} />);
    expect(screen.getByText("Sin datos históricos para este medidor.")).toBeInTheDocument();
    expect(screen.queryByTestId("mock-echarts")).not.toBeInTheDocument();
  });

  it("renders a single grid for consumption only when compare mode is off", () => {
    render(<MeterHistoryChart readings={readings} baselineKwh={100} />);
    const chart = screen.getByTestId("mock-echarts");
    const option = JSON.parse(chart.getAttribute("data-option") as string);
    expect(option.series).toHaveLength(1);
    expect(option.series[0].name).toBe("Consumo (kWh)");
  });

  it("adds a baseline markLine when baselineKwh is provided", () => {
    render(<MeterHistoryChart readings={readings} baselineKwh={100} />);
    const chart = screen.getByTestId("mock-echarts");
    const option = JSON.parse(chart.getAttribute("data-option") as string);
    expect(option.series[0].markLine.data).toEqual(
      expect.arrayContaining([expect.objectContaining({ yAxis: 100 })])
    );
  });

  it("adds event markLines when events are provided", () => {
    render(<MeterHistoryChart readings={readings} baselineKwh={null} events={events} />);
    const chart = screen.getByTestId("mock-echarts");
    const option = JSON.parse(chart.getAttribute("data-option") as string);
    expect(option.series[0].markLine.data).toEqual(
      expect.arrayContaining([expect.objectContaining({ xAxis: "2026-09-01T00:30:00Z" })])
    );
  });

  it("enables compare mode and overlays the selected variable on a single grid with its own y-axis", async () => {
    const user = userEvent.setup();
    render(<MeterHistoryChart readings={readings} baselineKwh={null} />);

    await user.click(screen.getByTestId("toggle-compare"));

    const chart = screen.getByTestId("mock-echarts");
    const option = JSON.parse(chart.getAttribute("data-option") as string);
    // consumption_kwh + default selected voltage_v
    expect(option.series).toHaveLength(2);
    // Un único grid (no apilados) — todas las series comparten el
    // mismo espacio visual, cada una con su propio eje Y superpuesto.
    expect(Array.isArray(option.grid)).toBe(false);
    expect(option.yAxis).toHaveLength(2);
    expect(option.series[0].yAxisIndex).toBe(0);
    expect(option.series[1].yAxisIndex).toBe(1);
    // Un único eje X compartido, no uno por variable.
    expect(Array.isArray(option.xAxis)).toBe(false);
  });

  it("toggles additional variable chips without emptying the selection (RN-02)", async () => {
    const user = userEvent.setup();
    render(<MeterHistoryChart readings={readings} baselineKwh={null} />);
    await user.click(screen.getByTestId("toggle-compare"));

    const voltageChip = screen.getByTestId("chip-voltage_v");
    expect(voltageChip).toHaveAttribute("aria-pressed", "true");

    // Trying to deselect the only selected chip must not empty the selection
    await user.click(voltageChip);
    expect(voltageChip).toHaveAttribute("aria-pressed", "true");

    // Selecting an additional chip works and both appear as series
    const currentChip = screen.getByTestId("chip-current_a");
    await user.click(currentChip);
    expect(currentChip).toHaveAttribute("aria-pressed", "true");

    const chart = screen.getByTestId("mock-echarts");
    const option = JSON.parse(chart.getAttribute("data-option") as string);
    expect(option.series).toHaveLength(3);
  });

  it("never passes CSS var() references as ECharts colors (canvas cannot resolve them)", () => {
    render(<MeterHistoryChart readings={readings} baselineKwh={100} events={events} />);
    const chart = screen.getByTestId("mock-echarts");
    const optionJson = chart.getAttribute("data-option") as string;
    expect(optionJson).not.toContain("var(--");
  });
});
