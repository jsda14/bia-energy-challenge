import { useState, useMemo } from "react";
import ReactECharts from "echarts-for-react";
import { CHART_COLOR_SERIES_A, CHART_COLOR_SERIES_B, CHART_COLOR_SERIES_C, CHART_COLOR_SERIES_D, CHART_COLOR_BASELINE } from "./chartColors";
import styles from "./MeterHistoryChart.module.css";
import type { Reading, Event } from "../../domain/types";

export type ChartVariable = "consumption_kwh" | "voltage_v" | "current_a" | "power_factor";

interface MeterHistoryChartProps {
  readings: Reading[];
  baselineKwh: number | null;
  highlightStart?: string;
  highlightEnd?: string;
  events?: Event[];
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

export function MeterHistoryChart({ readings, baselineKwh, highlightStart, highlightEnd, events = [] }: MeterHistoryChartProps) {
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

    const gridCount = variables.length;
    const gridHeight = 85 / gridCount; // leaving some space at top/bottom

    const grids = variables.map((_, index) => ({
      left: "3%",
      right: "4%",
      top: `${5 + index * gridHeight}%`,
      height: `${gridHeight - 5}%`,
      containLabel: true,
    }));

    const xAxes = variables.map((_, index) => ({
      type: "category",
      gridIndex: index,
      boundaryGap: false,
      data: dates,
      axisLabel: {
        show: index === gridCount - 1, // Only show labels on the bottom-most grid
        formatter: (value: string) => {
          const date = new Date(value);
          return `${date.getDate()} ${date.toLocaleString('es-ES', { month: 'short' })}, ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        },
      },
      axisTick: { show: index === gridCount - 1 },
      axisLine: { show: true },
    }));

    const yAxes = variables.map((variable, index) => ({
      type: "value",
      gridIndex: index,
      name: VARIABLE_LABELS[variable],
      nameLocation: "middle",
      nameGap: 35,
      splitLine: { show: true },
    }));

    const series = variables.map((variable, index) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const s: any = {
        name: VARIABLE_LABELS[variable],
        type: "line",
        data: readings.map((r) => r[variable]),
        xAxisIndex: index,
        yAxisIndex: index,
        itemStyle: { color: SERIES_COLORS[index] },
        lineStyle: { color: SERIES_COLORS[index] },
        showSymbol: false,
      };

      if (variable === "consumption_kwh" && baselineKwh !== null) {
        s.markLine = {
          data: [{ yAxis: baselineKwh, name: "Baseline" }],
          itemStyle: { color: CHART_COLOR_BASELINE },
          lineStyle: { color: CHART_COLOR_BASELINE },
          label: { formatter: 'Baseline' },
        };
      }

      if (variable === "consumption_kwh" && highlightStart && highlightEnd) {
        s.markArea = {
          data: [[{ xAxis: highlightStart }, { xAxis: highlightEnd }]],
          itemStyle: {
            color: "rgba(114, 28, 36, 0.15)"
          }
        };
      }

      if (variable === "consumption_kwh" && events.length > 0) {
        if (!s.markLine) s.markLine = { data: [] };
        const eventMarks = events.map((e) => ({
          xAxis: e.event_timestamp,
          name: e.event_type,
          label: { formatter: e.event_type, position: 'insideStartTop' },
          lineStyle: { color: "#eab308", type: "dashed" },
        }));
        s.markLine.data = [...s.markLine.data, ...eventMarks];
      }

      return s;
    });

    return {
      tooltip: { 
        trigger: "axis",
        axisPointer: { type: 'cross' }
      },
      axisPointer: {
        link: [{ xAxisIndex: 'all' }],
      },
      legend: { 
        data: variables.map((v) => VARIABLE_LABELS[v]),
        top: 0,
      },
      grid: grids,
      xAxis: xAxes,
      yAxis: yAxes,
      series,
    };
  }, [readings, compareMode, selectedOtherVariables, baselineKwh, highlightStart, highlightEnd, events]);

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
        style={{ height: `${compareMode ? 400 + selectedOtherVariables.length * 150 : 400}px`, width: "100%" }} 
      />
    </div>
  );
}
