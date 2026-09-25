import { useDashboardSummary } from "../api/queries/useDashboardSummary";
import { useMeters } from "../api/queries/useMeters";
import { formatDateTime, formatKwh } from "../domain/formatting";
import { StatCard } from "../components/ui/StatCard";
import { RunAnalysisButton } from "../components/ui/RunAnalysisButton";
import styles from "./DashboardPage.module.css";

export default function DashboardPage() {
  const { data: dashboardSummary, isLoading, isError } = useDashboardSummary();
  const { data: meters, isLoading: metersLoading, isError: metersError } = useMeters();

  if (isLoading) {
    return <div>Cargando...</div>;
  }

  if (isError || !dashboardSummary) {
    return <div>Error al cargar el dashboard.</div>;
  }

  let totalConsumptionDisplay = "—";
  if (metersLoading) {
    totalConsumptionDisplay = "Cargando...";
  } else if (!metersError && meters) {
    const total = meters.reduce((acc, m) => acc + m.consumption_kwh, 0);
    totalConsumptionDisplay = formatKwh(total);
  }

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
    </div>
  );
}
