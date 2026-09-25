import { useState, useMemo } from "react";
import ReactECharts from "echarts-for-react";
import { CHART_COLOR_SERIES_A, CHART_COLOR_SERIES_B, CHART_COLOR_SERIES_C, CHART_COLOR_SERIES_D, CHART_COLOR_BASELINE } from "./chartColors";
import styles from "./MeterHistoryChart.module.css";
import type { Reading } from "../../domain/types";

export type ChartVariable = "consumption_kwh" | "voltage_v" | "current_a" | "power_factor";

interface MeterHistoryChartProps {
  readings: Reading[];
  baselineKwh: number | null;
  highlightStart?: string;
  highlightEnd?: string;
}

const VARIABLE_LABELS: Record<ChartVariable, string> = {
  consumption_kwh: "Consumo (kWh)",
  voltage_v: "Voltaje (V)",
  current_a: "Corriente (A)",
  power_factor: "Factor de potencia",
};

const SERIES_COLORS = [
  CHART_COLOR_SERIES_A,
  CHART_COLOR_SERIES_B,
  CHART_COLOR_SERIES_C,
  CHART_COLOR_SERIES_D,
];

export function MeterHistoryChart({ readings, baselineKwh, highlightStart, highlightEnd }: MeterHistoryChartProps) {
  const [compareMode, setCompareMode] = useState(false);
  const [selectedOtherVariables, setSelectedOtherVariables] = useState<ChartVariable[]>(["voltage_v"]);

  const toggleOtherVariable = (variable: ChartVariable) => {
    setSelectedOtherVariables((prev) => {
      if (prev.includes(variable)) {
        // RN-02: nunca deja la selección vacía mientras compareMode esté activo.
        if (prev.length === 1) return prev;
        return prev.filter((v) => v !== variable);
      }
      return [...prev, variable];
    });
  };

  const chartOptions = useMemo(() => {
    const dates = readings.map((r) => r.timestamp);
    const variables: ChartVariable[] = compareMode 
      ? ["consumption_kwh", ...selectedOtherVariables] 
      : ["consumption_kwh"];

    const yAxis = variables.map((variable, index) => ({
      type: "value",
      name: VARIABLE_LABELS[variable],
      position: index % 2 === 0 ? "left" : "right",
      offset: Math.floor(index / 2) * 50,
      nameLocation: "end",
    }));

    const series = variables.map((variable, index) => {
      const s: Record<string, unknown> = {
        name: VARIABLE_LABELS[variable],
        type: "line",
        data: readings.map((r) => r[variable]),
        yAxisIndex: index,
        itemStyle: { color: SERIES_COLORS[index] },
        lineStyle: { color: SERIES_COLORS[index] },
      };

      if (variable === "consumption_kwh" && baselineKwh !== null) {
        s.markLine = {
          data: [{ yAxis: baselineKwh, name: "Baseline" }],
          itemStyle: { color: CHART_COLOR_BASELINE },
          lineStyle: { color: CHART_COLOR_BASELINE },
        };
      }

      if (highlightStart && highlightEnd) {
        s.markArea = {
          data: [[{ xAxis: highlightStart }, { xAxis: highlightEnd }]],
          itemStyle: {
            color: "rgba(114, 28, 36, 0.15)"
          }
        };
      }

      return s;
    });

    return {
      tooltip: { trigger: "axis" },
      legend: { data: variables.map((v) => VARIABLE_LABELS[v]) },
      grid: { top: "15%", left: "3%", right: "4%", bottom: "15%", containLabel: true },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: dates,
      },
      yAxis,
      series,
    };
  }, [readings, compareMode, selectedOtherVariables, baselineKwh, highlightStart, highlightEnd]);

  if (readings.length === 0) {
    return <div className={styles.empty}>Sin datos históricos para este medidor.</div>;
  }

  const otherVariables = (Object.entries(VARIABLE_LABELS) as [ChartVariable, string][]).filter(
    ([key]) => key !== "consumption_kwh"
  );

  return (
    <div className={styles.chartContainer}>
      <div className={styles.controls}>
        <div className={styles.controlGroup}>
          <input
            type="checkbox"
            id="compare-mode"
            checked={compareMode}
            onChange={(e) => setCompareMode(e.target.checked)}
            data-testid="toggle-compare"
          />
          <label htmlFor="compare-mode" className={styles.label}>Comparar variables</label>
        </div>

        {compareMode && (
          <div className={styles.controlGroup}>
            <span className={styles.label}>Variables:</span>
            <div className={styles.chipGroup} role="group" aria-label="Variables a comparar">
              {otherVariables.map(([key, label]) => {
                const isSelected = selectedOtherVariables.includes(key);
                return (
                  <button
                    key={key}
                    type="button"
                    className={`${styles.chip} ${isSelected ? styles["chip--selected"] : ""}`}
                    aria-pressed={isSelected}
                    onClick={() => toggleOtherVariable(key)}
                    data-testid={`chip-${key}`}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <ReactECharts 
        option={chartOptions} 
        notMerge={true}
        style={{ height: "400px", width: "100%" }} 
      />
    </div>
  );
}
