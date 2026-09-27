import { useState, useMemo } from "react";
import ReactECharts from "echarts-for-react";
import { CHART_COLOR_SERIES_A, CHART_COLOR_SERIES_B, CHART_COLOR_SERIES_C, CHART_COLOR_SERIES_D, CHART_COLOR_BASELINE, CHART_COLOR_HIGHLIGHT_AREA } from "./chartColors";
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

  const variables: ChartVariable[] = useMemo(
    () => (compareMode ? ["consumption_kwh", ...selectedOtherVariables] : ["consumption_kwh"]),
    [compareMode, selectedOtherVariables]
  );

  // Ancho mínimo del chart: con varios ejes Y apilados a la izquierda,
  // comprimir el chart al 100% del contenedor en mobile dejaba muy
  // poco espacio real para las líneas de datos (ver captura real:
  // "espacio en blanco feo" antes del área de datos). En vez de
  // seguir comprimiendo, el chart tiene un ancho mínimo fijo y el
  // contenedor scrollea horizontalmente — mismo patrón ya usado en el
  // proyecto para tablas anchas en mobile (`overflow-x: auto`).
  const chartMinWidth = 320 + Math.max(0, variables.length - 1) * 70;

  const chartOptions = useMemo(() => {
    const dates = readings.map((r) => r.timestamp);

    // Un único grid: todas las series se superponen en el mismo
    // espacio visual (comparables directamente entre sí), en vez de
    // grids apilados verticalmente que se leían como gráficas
    // independientes. Cada variable tiene su propio eje Y con su
    // propia escala — el primero a la izquierda del grid, los
    // siguientes también a la izquierda pero desplazados hacia afuera
    // vía `offset` para no solaparse entre sí (patrón estándar de
    // ECharts para múltiples ejes Y sobre un único grid).
    //
    // `grid.left` debe estar en la MISMA unidad (px) que `offset` de
    // cada eje — mezclar offset en px con un left en % hizo que, con
    // 3+ variables, el grid completo quedara empujado fuera del área
    // visible (bug real encontrado al verificar con 3 variables
    // superpuestas: el chart se veía vacío, solo los ejes visibles).
    // yAxisOffsetStep debe ser mayor que nameGap (45px) + el ancho
    // aproximado del texto rotado del nombre del eje — con offset
    // menor o igual a ese espacio, el nombre de un eje invade el
    // área del eje siguiente y se superponen entre sí (bug real
    // confirmado con 3 ejes: "Voltaje (V)" se solapaba con "Factor de
    // potencia" al no dejar margen suficiente entre ambos).
    const yAxisOffsetStep = 70; // px entre cada eje Y adicional
    const leftPaddingPx = 50 + Math.max(0, variables.length - 1) * yAxisOffsetStep;

    const yAxes = variables.map((variable, index) => ({
      type: "value" as const,
      name: VARIABLE_LABELS[variable],
      nameLocation: "middle" as const,
      nameGap: 40,
      position: "left" as const,
      offset: index * yAxisOffsetStep,
      axisLine: { show: true, lineStyle: { color: SERIES_COLORS[index] } },
      axisLabel: { color: SERIES_COLORS[index] },
      splitLine: { show: index === 0 },
    }));

    const series = variables.map((variable, index) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const s: any = {
        name: VARIABLE_LABELS[variable],
        type: "line",
        data: readings.map((r) => r[variable]),
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
            color: CHART_COLOR_HIGHLIGHT_AREA
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
      legend: {
        data: variables.map((v) => VARIABLE_LABELS[v]),
        top: 0,
      },
      grid: {
        left: leftPaddingPx,
        right: "4%",
        top: "12%",
        bottom: "12%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: dates,
        axisLabel: {
          formatter: (value: string) => {
            const date = new Date(value);
            return `${date.getDate()} ${date.toLocaleString('es-ES', { month: 'short' })}, ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
          },
        },
      },
      yAxis: yAxes,
      series,
    };
  }, [readings, variables, baselineKwh, highlightStart, highlightEnd, events]);

  if (readings.length === 0) {
    return <div className={styles["meter-history-chart__empty"]}>Sin datos históricos para este medidor.</div>;
  }

  const otherVariables = (Object.entries(VARIABLE_LABELS) as [ChartVariable, string][]).filter(
    ([key]) => key !== "consumption_kwh"
  );

  return (
    <div className={styles["meter-history-chart__chart-container"]}>
      <div className={styles["meter-history-chart__controls"]}>
        <div className={styles["meter-history-chart__control-group"]}>
          <input
            type="checkbox"
            id="compare-mode"
            checked={compareMode}
            onChange={(e) => setCompareMode(e.target.checked)}
            data-testid="toggle-compare"
          />
          <label htmlFor="compare-mode" className={styles["meter-history-chart__label"]}>Comparar variables</label>
        </div>

        {compareMode && (
          <div className={styles["meter-history-chart__control-group"]}>
            <span className={styles["meter-history-chart__label"]}>Variables:</span>
            <div className={styles["meter-history-chart__chip-group"]} role="group" aria-label="Variables a comparar">
              {otherVariables.map(([key, label]) => {
                const isSelected = selectedOtherVariables.includes(key);
                return (
                  <button
                    key={key}
                    type="button"
                    className={`${styles["meter-history-chart__chip"]} ${isSelected ? styles["meter-history-chart__chip--selected"] : ""}`}
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

      <div className={styles["meter-history-chart__chart-scroll"]}>
        <ReactECharts
          option={chartOptions}
          notMerge={true}
          style={{ height: "440px", width: "100%", minWidth: `${chartMinWidth}px` }}
        />
      </div>
    </div>
  );
}
