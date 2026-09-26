import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ConsumptionTimelineChart } from "./ConsumptionTimelineChart";
import type { ConsumptionTimelinePoint } from "../../domain/types";

// Mock echarts to avoid canvas rendering issues in jsdom
vi.mock("echarts-for-react", () => ({
  default: (props: { option: unknown }) => (
    <div data-testid="mock-echarts" data-option={JSON.stringify(props.option)} />
  ),
}));

const points: ConsumptionTimelinePoint[] = [
  { timestamp: "2026-09-01T00:00:00Z", total_consumption_kwh: 100.5 },
  { timestamp: "2026-09-02T00:00:00Z", total_consumption_kwh: 120.25 },
];

describe("ConsumptionTimelineChart", () => {
  it("renders the empty state when there are no points", () => {
    render(<ConsumptionTimelineChart points={[]} />);
    expect(screen.getByText("No hay datos de consumo disponibles.")).toBeInTheDocument();
    expect(screen.queryByTestId("mock-echarts")).not.toBeInTheDocument();
  });

  it("renders the chart with the aggregated series data", () => {
    render(<ConsumptionTimelineChart points={points} />);
    const chart = screen.getByTestId("mock-echarts");
    const option = JSON.parse(chart.getAttribute("data-option") as string);

    expect(option.xAxis.data).toEqual(["2026-09-01T00:00:00Z", "2026-09-02T00:00:00Z"]);
    expect(option.series[0].data).toEqual([100.5, 120.25]);
  });

  it("never passes CSS var() references as ECharts colors (canvas cannot resolve them)", () => {
    render(<ConsumptionTimelineChart points={points} />);
    const chart = screen.getByTestId("mock-echarts");
    const optionJson = chart.getAttribute("data-option") as string;
    expect(optionJson).not.toContain("var(--");
  });
});
