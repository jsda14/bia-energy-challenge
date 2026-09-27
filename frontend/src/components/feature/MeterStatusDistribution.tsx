import ReactECharts from "echarts-for-react";
import { useMemo } from "react";
import type { MeterSummary } from "../../domain/types";
import {
  CHART_COLOR_STATUS_HEALTHY,
  CHART_COLOR_STATUS_WARNING,
  CHART_COLOR_STATUS_CRITICAL,
} from "./chartColors";
import styles from "./MeterStatusDistribution.module.css";

interface MeterStatusDistributionProps {
  meters: MeterSummary[];
}

export function MeterStatusDistribution({ meters }: MeterStatusDistributionProps) {
  const chartOptions = useMemo(() => {
    let healthy = 0;
    let warning = 0;
    let critical = 0;

    meters.forEach((m) => {
      if (m.status === "Critical" || m.anomaly_severity === "HIGH") {
        critical++;
      } else if (m.status === "Alert" || m.anomaly_severity === "MEDIUM" || m.anomaly_severity === "LOW") {
        warning++;
      } else {
        healthy++;
      }
    });

    return {
      tooltip: {
        trigger: "item"
      },
      legend: {
        bottom: "0",
        left: "center"
      },
      series: [
        {
          name: "Estado",
          type: "pie",
          radius: ["40%", "70%"],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 4,
            borderWidth: 2
          },
          label: {
            show: false,
            position: "center"
          },
          labelLine: {
            show: false
          },
          data: [
            { value: healthy, name: "Sanos", itemStyle: { color: CHART_COLOR_STATUS_HEALTHY } },
            { value: warning, name: "En Alerta", itemStyle: { color: CHART_COLOR_STATUS_WARNING } },
            { value: critical, name: "Críticos", itemStyle: { color: CHART_COLOR_STATUS_CRITICAL } }
          ].filter(d => d.value > 0)
        }
      ]
    };
  }, [meters]);

  if (meters.length === 0) {
    return null;
  }

  return (
    <div className={styles["meter-status-distribution__container"]}>
      <h3 className={styles["meter-status-distribution__title"]}>Estado de Medidores</h3>
      <ReactECharts option={chartOptions} style={{ height: "300px", width: "100%" }} />
    </div>
  );
}
