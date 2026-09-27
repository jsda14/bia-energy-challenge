import ReactECharts from "echarts-for-react";
import { useMemo } from "react";
import type { ConsumptionTimelinePoint } from "../../domain/types";
import { formatKwh } from "../../domain/formatting";
import { CHART_COLOR_SERIES_A } from "./chartColors";
import styles from "./ConsumptionTimelineChart.module.css";

interface ConsumptionTimelineChartProps {
  points: ConsumptionTimelinePoint[];
}

export function ConsumptionTimelineChart({ points }: ConsumptionTimelineChartProps) {
  const chartOptions = useMemo(() => {
    return {
      tooltip: {
        trigger: "axis",
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        formatter: (params: any[]) => {
          const point = params[0];
          const date = new Date(point.axisValue);
          const dateStr = `${date.getDate()} ${date.toLocaleString('es-ES', { month: 'short' })}, ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
          return `${dateStr}<br/><b>${formatKwh(point.data)}</b>`;
        }
      },
      grid: { top: "10%", left: "2%", right: "2%", bottom: "10%", containLabel: true },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: points.map((p) => p.timestamp),
        axisLabel: {
          formatter: (value: string) => {
            const date = new Date(value);
            return `${date.getDate()} ${date.toLocaleString('es-ES', { month: 'short' })}, ${date.getHours().toString().padStart(2, '0')}:00`;
          },
        },
      },
      yAxis: {
        type: "value",
      },
      series: [
        {
          name: "Consumo Total",
          type: "line",
          data: points.map((p) => p.total_consumption_kwh),
          itemStyle: { color: CHART_COLOR_SERIES_A },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: `${CHART_COLOR_SERIES_A}66` }, // 40% alpha
                { offset: 1, color: `${CHART_COLOR_SERIES_A}00` }  // 0% alpha
              ]
            }
          },
          smooth: true,
          showSymbol: false,
        },
      ],
    };
  }, [points]);

  if (points.length === 0) {
    return <div className={styles["consumption-timeline-chart__empty"]}>No hay datos de consumo disponibles.</div>;
  }

  return (
    <div className={styles["consumption-timeline-chart__container"]}>
      <h3 className={styles["consumption-timeline-chart__title"]}>Consumo Total (kWh)</h3>
      <ReactECharts option={chartOptions} style={{ height: "350px", width: "100%" }} />
    </div>
  );
}
