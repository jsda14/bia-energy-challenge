import { useNavigate } from "react-router-dom";
import type { AnomalySummary } from "../../domain/types";
import { formatDateTime, severityToColorToken } from "../../domain/formatting";
import { Badge } from "../ui/Badge";
import styles from "./TriageList.module.css";

interface TriageListProps {
  anomalies: AnomalySummary[];
}

export function TriageList({ anomalies }: TriageListProps) {
  const navigate = useNavigate();
  
  // Sort by severity and detected_at (most recent first)
  const sorted = [...anomalies].sort((a, b) => {
    const severityOrder = { "HIGH": 3, "MEDIUM": 2, "LOW": 1 };
    const sA = severityOrder[a.severity as keyof typeof severityOrder] || 0;
    const sB = severityOrder[b.severity as keyof typeof severityOrder] || 0;
    if (sA !== sB) return sB - sA;
    return new Date(b.detected_at).getTime() - new Date(a.detected_at).getTime();
  }).slice(0, 5); // Take top 5

  if (sorted.length === 0) {
    return (
      <div className={styles["triage-list__container"]}>
        <h3 className={styles["triage-list__title"]}>Triage (Top Anomalías)</h3>
        <p className={styles["triage-list__empty"]}>No hay anomalías activas.</p>
      </div>
    );
  }

  return (
    <div className={styles["triage-list__container"]}>
      <h3 className={styles["triage-list__title"]}>Triage (Top Anomalías)</h3>
      <ul className={styles["triage-list__list"]}>
        {sorted.map(anomaly => (
          <li 
            key={anomaly.id} 
            className={styles["triage-list__item"]}
            onClick={() => navigate(`/anomalies/${anomaly.id}`)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                navigate(`/anomalies/${anomaly.id}`);
              }
            }}
          >
            <div className={styles["triage-list__item-header"]}>
              <Badge label={anomaly.severity} tone={severityToColorToken(anomaly.severity)} />
              <span className={styles["triage-list__date"]}>{formatDateTime(anomaly.detected_at)}</span>
            </div>
            <div className={styles["triage-list__item-body"]}>
              <span className={styles["triage-list__meter-id"]}>{anomaly.meter_id}</span>
              <span className={styles["triage-list__type"]}>{anomaly.type}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
