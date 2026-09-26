import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MeterStatusDistribution } from "./MeterStatusDistribution";
import type { MeterSummary } from "../../domain/types";

// Mock echarts to avoid canvas rendering issues in jsdom
vi.mock("echarts-for-react", () => ({
  default: (props: { option: unknown }) => (
    <div data-testid="mock-echarts" data-option={JSON.stringify(props.option)} />
  ),
}));

function makeMeter(overrides: Partial<MeterSummary>): MeterSummary {
  return {
    meter_id: "M-1",
    name: "Meter 1",
    status: "OK",
    consumption_kwh: 100,
    variation_pct: null,
    anomaly_severity: null,
    ...overrides,
  };
}

describe("MeterStatusDistribution", () => {
  it("renders nothing when there are no meters", () => {
    const { container } = render(<MeterStatusDistribution meters={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("classifies meters into healthy, warning and critical buckets", () => {
    const meters: MeterSummary[] = [
      makeMeter({ meter_id: "M-1", status: "OK", anomaly_severity: null }),
      makeMeter({ meter_id: "M-2", status: "Alert", anomaly_severity: "MEDIUM" }),
      makeMeter({ meter_id: "M-3", status: "Critical", anomaly_severity: "HIGH" }),
    ];
    render(<MeterStatusDistribution meters={meters} />);

    const chart = screen.getByTestId("mock-echarts");
    const option = JSON.parse(chart.getAttribute("data-option") as string);
    const pieData = option.series[0].data;

    expect(pieData).toEqual([
      { value: 1, name: "Sanos", itemStyle: { color: "#B3AFDD" } },
      { value: 1, name: "En Alerta", itemStyle: { color: "#F2C572" } },
      { value: 1, name: "Críticos", itemStyle: { color: "#F5A9BE" } },
    ]);
  });

  it("filters out buckets with zero count", () => {
    const meters: MeterSummary[] = [
      makeMeter({ meter_id: "M-1", status: "OK", anomaly_severity: null }),
      makeMeter({ meter_id: "M-2", status: "OK", anomaly_severity: null }),
    ];
    render(<MeterStatusDistribution meters={meters} />);

    const chart = screen.getByTestId("mock-echarts");
    const option = JSON.parse(chart.getAttribute("data-option") as string);
    const pieData = option.series[0].data;

    expect(pieData).toEqual([
      { value: 2, name: "Sanos", itemStyle: { color: "#B3AFDD" } },
    ]);
  });

  it("never passes CSS var() references as ECharts colors (canvas cannot resolve them)", () => {
    const meters: MeterSummary[] = [
      makeMeter({ meter_id: "M-1", status: "Critical", anomaly_severity: "HIGH" }),
    ];
    render(<MeterStatusDistribution meters={meters} />);

    const chart = screen.getByTestId("mock-echarts");
    const optionJson = chart.getAttribute("data-option") as string;
    expect(optionJson).not.toContain("var(--");
  });

  it("renders the section title", () => {
    render(<MeterStatusDistribution meters={[makeMeter({})]} />);
    expect(screen.getByText("Estado de Medidores")).toBeInTheDocument();
  });
});
