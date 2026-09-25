import { useDashboardSummary } from "../api/queries/useDashboardSummary";
import { formatDateTime } from "../domain/formatting";
import { StatCard } from "../components/ui/StatCard";
import { RunAnalysisButton } from "../components/ui/RunAnalysisButton";
import styles from "./DashboardPage.module.css";

export default function DashboardPage() {
  const { data: dashboardSummary, isLoading, isError } = useDashboardSummary();

  if (isLoading) {
    return <div>Cargando...</div>;
  }

  if (isError || !dashboardSummary) {
    return <div>Error al cargar el dashboard.</div>;
  }

  return (
    <div className={styles.dashboard}>
      <div className={styles.dashboard__header}>
        <h1>Dashboard</h1>
        <RunAnalysisButton meterId={null} />
      </div>

      <div className={styles["dashboard__stats-grid"]}>
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
