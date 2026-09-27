import { triageStatusToLabel } from "../../domain/formatting";
import styles from "./AnomaliesFilterBar.module.css";

interface AnomaliesFilterBarProps {
  meterIdOptions: string[];
  typeOptions: string[];
  severityOptions: string[];
  triageStatusOptions: string[];
  selectedMeterId: string | null;
  selectedType: string | null;
  selectedSeverity: string | null;
  selectedTriageStatus: string | null;
  onMeterIdChange: (meterId: string | null) => void;
  onTypeChange: (type: string | null) => void;
  onSeverityChange: (severity: string | null) => void;
  onTriageStatusChange: (triageStatus: string | null) => void;
}

export function AnomaliesFilterBar({
  meterIdOptions,
  typeOptions,
  severityOptions,
  triageStatusOptions,
  selectedMeterId,
  selectedType,
  selectedSeverity,
  selectedTriageStatus,
  onMeterIdChange,
  onTypeChange,
  onSeverityChange,
  onTriageStatusChange,
}: AnomaliesFilterBarProps) {
  return (
    <div className={styles["anomalies-filter-bar"]}>
      <div className={styles["anomalies-filter-bar__filter-group"]}>
        <label htmlFor="meterId-filter" className={styles["anomalies-filter-bar__label"]}>
          Medidor:
        </label>
        <select
          id="meterId-filter"
          className={styles["anomalies-filter-bar__select"]}
          value={selectedMeterId || ""}
          onChange={(e) => onMeterIdChange(e.target.value || null)}
        >
          <option value="">Todos</option>
          {meterIdOptions.map((meterId) => (
            <option key={meterId} value={meterId}>
              {meterId}
            </option>
          ))}
        </select>
      </div>

      <div className={styles["anomalies-filter-bar__filter-group"]}>
        <label htmlFor="type-filter" className={styles["anomalies-filter-bar__label"]}>
          Tipo:
        </label>
        <select
          id="type-filter"
          className={styles["anomalies-filter-bar__select"]}
          value={selectedType || ""}
          onChange={(e) => onTypeChange(e.target.value || null)}
        >
          <option value="">Todos</option>
          {typeOptions.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </div>

      <div className={styles["anomalies-filter-bar__filter-group"]}>
        <label htmlFor="severity-filter" className={styles["anomalies-filter-bar__label"]}>
          Severidad:
        </label>
        <select
          id="severity-filter"
          className={styles["anomalies-filter-bar__select"]}
          value={selectedSeverity || ""}
          onChange={(e) => onSeverityChange(e.target.value || null)}
        >
          <option value="">Todas</option>
          {severityOptions.map((severity) => (
            <option key={severity} value={severity}>
              {severity}
            </option>
          ))}
        </select>
      </div>

      <div className={styles["anomalies-filter-bar__filter-group"]}>
        <label htmlFor="triageStatus-filter" className={styles["anomalies-filter-bar__label"]}>
          Estado de Triage:
        </label>
        <select
          id="triageStatus-filter"
          className={styles["anomalies-filter-bar__select"]}
          value={selectedTriageStatus || ""}
          onChange={(e) => onTriageStatusChange(e.target.value || null)}
        >
          <option value="">Todas</option>
          {triageStatusOptions.map((triageStatus) => (
            <option key={triageStatus} value={triageStatus}>
              {triageStatusToLabel(triageStatus)}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
