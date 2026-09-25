import { useState, useMemo } from "react";
import ReactECharts from "echarts-for-react";
import { CHART_COLOR_SERIES_A, CHART_COLOR_SERIES_B, CHART_COLOR_BASELINE } from "./chartColors";
import styles from "./MeterHistoryChart.module.css";
import type { Reading } from "../../domain/types";

export type ChartVariable = "consumption_kwh" | "voltage_v" | "current_a" | "power_factor";

interface MeterHistoryChartProps {
  readings: Reading[];
  baselineKwh: number | null;
}

const VARIABLE_LABELS: Record<ChartVariable, string> = {
  consumption_kwh: "Consumo (kWh)",
  voltage_v: "Voltaje (V)",
  current_a: "Corriente (A)",
  power_factor: "Factor de potencia",
};

export function MeterHistoryChart({ readings, baselineKwh }: MeterHistoryChartProps) {
  const [seriesA, setSeriesA] = useState<ChartVariable>("consumption_kwh");
  const [seriesB, setSeriesB] = useState<ChartVariable>("voltage_v");
  const [compareEnabled, setCompareEnabled] = useState(false);

  const chartOptions = useMemo(() => {
    const dates = readings.map((r) => r.timestamp);
    const dataA = readings.map((r) => r[seriesA]);
    const dataB = compareEnabled ? readings.map((r) => r[seriesB]) : [];

    const yAxis = [
      {
        type: "value",
        name: VARIABLE_LABELS[seriesA],
        position: "left",
      },
    ];

    if (compareEnabled) {
      yAxis.push({
        type: "value",
        name: VARIABLE_LABELS[seriesB],
        position: "right",
      });
    }

    const series: Array<Record<string, unknown>> = [
      {
        name: VARIABLE_LABELS[seriesA],
        type: "line",
        data: dataA,
        yAxisIndex: 0,
        itemStyle: { color: CHART_COLOR_SERIES_A },
        lineStyle: { color: CHART_COLOR_SERIES_A },
      },
    ];

    if (seriesA === "consumption_kwh" && baselineKwh !== null) {
      series[0].markLine = {
        data: [{ yAxis: baselineKwh, name: "Baseline" }],
        itemStyle: { color: CHART_COLOR_BASELINE },
        lineStyle: { color: CHART_COLOR_BASELINE },
      };
    }

    if (compareEnabled) {
      series.push({
        name: VARIABLE_LABELS[seriesB],
        type: "line",
        data: dataB,
        yAxisIndex: 1,
        itemStyle: { color: CHART_COLOR_SERIES_B },
        lineStyle: { color: CHART_COLOR_SERIES_B },
      });
    }

    return {
      tooltip: { trigger: "axis" },
      legend: { data: compareEnabled ? [VARIABLE_LABELS[seriesA], VARIABLE_LABELS[seriesB]] : [VARIABLE_LABELS[seriesA]] },
      grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: dates,
      },
      yAxis,
      series,
    };
  }, [readings, seriesA, seriesB, compareEnabled, baselineKwh]);

  if (readings.length === 0) {
    return <div className={styles.empty}>Sin datos históricos para este medidor.</div>;
  }

  return (
    <div className={styles.chartContainer}>
      <div className={styles.controls}>
        <div className={styles.controlGroup}>
          <label htmlFor="series-a" className={styles.label}>Serie A:</label>
          <select
            id="series-a"
            className={styles.select}
            value={seriesA}
            onChange={(e) => setSeriesA(e.target.value as ChartVariable)}
            data-testid="select-series-a"
          >
            {(Object.entries(VARIABLE_LABELS) as [ChartVariable, string][]).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
        </div>

        <div className={styles.controlGroup}>
          <label htmlFor="compare-toggle" className={styles.label}>Comparar dos variables</label>
          <input
            type="checkbox"
            id="compare-toggle"
            checked={compareEnabled}
            onChange={(e) => setCompareEnabled(e.target.checked)}
            data-testid="toggle-compare"
          />
        </div>

        {compareEnabled && (
          <div className={styles.controlGroup}>
            <label htmlFor="series-b" className={styles.label}>Serie B:</label>
            <select
              id="series-b"
              className={styles.select}
              value={seriesB}
              onChange={(e) => setSeriesB(e.target.value as ChartVariable)}
              data-testid="select-series-b"
            >
              {(Object.entries(VARIABLE_LABELS) as [ChartVariable, string][]).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      <ReactECharts option={chartOptions} style={{ height: "400px", width: "100%" }} />
    </div>
  );
}
