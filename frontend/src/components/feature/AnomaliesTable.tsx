import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { AnomalySummary } from "../../domain/types";
import { formatDateTime, severityToColorToken } from "../../domain/formatting";
import { Badge } from "../ui/Badge";
import styles from "./AnomaliesTable.module.css";

export type AnomalySortableColumn = "meter_id" | "type" | "severity" | "confidence" | "detected_at";
type SortDirection = "asc" | "desc" | null;

interface AnomaliesTableProps {
  anomalies: AnomalySummary[];
}

export function AnomaliesTable({ anomalies }: AnomaliesTableProps) {
  const navigate = useNavigate();
  const [sortColumn, setSortColumn] = useState<AnomalySortableColumn | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  const handleSort = (column: AnomalySortableColumn) => {
    if (sortColumn === column) {
      if (sortDirection === "asc") setSortDirection("desc");
      else if (sortDirection === "desc") {
        setSortDirection(null);
        setSortColumn(null);
      }
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  const sortedAnomalies = [...anomalies].sort((a, b) => {
    if (!sortColumn || !sortDirection) return 0;

    const valA = a[sortColumn];
    const valB = b[sortColumn];

    if (valA < valB) return sortDirection === "asc" ? -1 : 1;
    if (valA > valB) return sortDirection === "asc" ? 1 : -1;
    return 0;
  });

  const getSortIcon = (column: AnomalySortableColumn) => {
    if (sortColumn !== column) return null;
    return sortDirection === "asc" ? " ▲" : " ▼";
  };

  const handleRowClick = (id: string) => {
    navigate(`/anomalies/${id}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent, id: string) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleRowClick(id);
    }
  };

  return (
    <div className={styles.tableWrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th className={styles.th}>
              <button type="button" className={styles.sortButton} onClick={() => handleSort("meter_id")}>
                Medidor{getSortIcon("meter_id")}
              </button>
            </th>
            <th className={styles.th}>
              <button type="button" className={styles.sortButton} onClick={() => handleSort("type")}>
                Tipo{getSortIcon("type")}
              </button>
            </th>
            <th className={styles.th}>
              <button type="button" className={styles.sortButton} onClick={() => handleSort("severity")}>
                Severidad{getSortIcon("severity")}
              </button>
            </th>
            <th className={styles.th}>
              <button type="button" className={styles.sortButton} onClick={() => handleSort("confidence")}>
                Confianza{getSortIcon("confidence")}
              </button>
            </th>
            <th className={styles.th}>
              <button type="button" className={styles.sortButton} onClick={() => handleSort("detected_at")}>
                Detectada{getSortIcon("detected_at")}
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedAnomalies.map((anomaly) => (
            <tr
              key={anomaly.id}
              className={styles.row}
              onClick={() => handleRowClick(anomaly.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => handleKeyDown(e, anomaly.id)}
              data-testid={`anomaly-row-${anomaly.id}`}
            >
              <td className={styles.td} data-label="Medidor">{anomaly.meter_id}</td>
              <td className={styles.td} data-label="Tipo">{anomaly.type}</td>
              <td className={styles.td} data-label="Severidad">
                <Badge label={anomaly.severity} tone={severityToColorToken(anomaly.severity)} />
              </td>
              <td className={styles.td} data-label="Confianza">{(anomaly.confidence * 100).toFixed(0)}%</td>
              <td className={styles.td} data-label="Detectada">{formatDateTime(anomaly.detected_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
