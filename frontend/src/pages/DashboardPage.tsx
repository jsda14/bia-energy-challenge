import { useDashboardSummary } from "../api/queries/useDashboardSummary";
import { useMeters } from "../api/queries/useMeters";
import { useAnomalies } from "../api/queries/useAnomalies";
import { useConsumptionTimeline } from "../api/queries/useConsumptionTimeline";
import { formatDateTime, formatKwh } from "../domain/formatting";
import { StatCard } from "../components/ui/StatCard";
import { RunAnalysisButton } from "../components/ui/RunAnalysisButton";
import { ConsumptionTimelineChart } from "../components/feature/ConsumptionTimelineChart";
import { MeterStatusDistribution } from "../components/feature/MeterStatusDistribution";
import { TriageList } from "../components/feature/TriageList";
import styles from "./DashboardPage.module.css";

export default function DashboardPage() {
  const { data: dashboardSummary, isLoading: summaryLoading, isError: summaryError } = useDashboardSummary();
  const { data: meters, isLoading: metersLoading, isError: metersError } = useMeters();
  const { data: anomalies, isLoading: anomaliesLoading, isError: anomaliesError } = useAnomalies();
  const { data: timeline, isLoading: timelineLoading, isError: timelineError } = useConsumptionTimeline();

  const isLoading = summaryLoading || metersLoading || anomaliesLoading || timelineLoading;
  const isError = summaryError || metersError || anomaliesError || timelineError;

  if (isLoading) {
    return <div>Cargando...</div>;
  }

  if (isError || !dashboardSummary || !meters || !anomalies || !timeline) {
    return <div>Error al cargar el dashboard.</div>;
  }

  const totalConsumptionDisplay = formatKwh(
    meters.reduce((acc, m) => acc + m.consumption_kwh, 0)
  );

  return (
    <div className={styles.dashboard}>
      <div className={styles.dashboard__header}>
        <h1>Dashboard</h1>
        <RunAnalysisButton meterId={null} />
      </div>

      <div className={styles["dashboard__stats-grid"]}>
        <StatCard
          label="Consumo Total"
          value={totalConsumptionDisplay}
          featured
        />

        <StatCard
          label="Anomalías detectadas"
          value={dashboardSummary.anomalies_detected.toString()}
        />
        
        <StatCard
          label="Alta prioridad"
          value={dashboardSummary.high_priority_count.toString()}
          tone={dashboardSummary.high_priority_count > 0 ? "warning" : "neutral"}
        />
        
        <StatCard
          label="Confianza promedio"
          value={
            dashboardSummary.average_confidence !== null
              ? `${(dashboardSummary.average_confidence * 100).toFixed(0)}%`
              : "—"
          }
        />
        
        <StatCard
          label="Última corrida"
          value={
            dashboardSummary.last_analysis_at !== null
              ? formatDateTime(dashboardSummary.last_analysis_at)
              : "Nunca"
          }
        />
      </div>

      <div className={styles.chartsGrid}>
        <div className={styles.mainChart}>
          <ConsumptionTimelineChart points={timeline.points} />
        </div>
        <div className={styles.sideColumn}>
          <MeterStatusDistribution meters={meters} />
        </div>
      </div>
      
      <div className={styles.fullWidthSection}>
        <TriageList anomalies={anomalies} />
      </div>
    </div>
  );
}
