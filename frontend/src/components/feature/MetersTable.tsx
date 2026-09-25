import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { MeterSummary } from "../../domain/types";
import { formatKwh, formatVariationPct, meterStatusToColorToken, severityToColorToken } from "../../domain/formatting";
import { Badge } from "../ui/Badge";
import styles from "./MetersTable.module.css";

type SortableColumn = "name" | "status" | "consumption_kwh" | "variation_pct" | "anomaly_severity";
type SortDirection = "asc" | "desc" | null;

interface MetersTableProps {
  meters: MeterSummary[];
}

export function MetersTable({ meters }: MetersTableProps) {
  const navigate = useNavigate();
  const [sortColumn, setSortColumn] = useState<SortableColumn | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  const handleSort = (column: SortableColumn) => {
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

  const sortedMeters = [...meters].sort((a, b) => {
    if (!sortColumn || !sortDirection) return 0;

    let valA = a[sortColumn];
    let valB = b[sortColumn];

    // Handle nulls
    if (valA === null) valA = sortDirection === "asc" ? Infinity : -Infinity;
    if (valB === null) valB = sortDirection === "asc" ? Infinity : -Infinity;

    if (valA < valB) return sortDirection === "asc" ? -1 : 1;
    if (valA > valB) return sortDirection === "asc" ? 1 : -1;
    return 0;
  });

  const getSortIcon = (column: SortableColumn) => {
    if (sortColumn !== column) return null;
    return sortDirection === "asc" ? " ▲" : " ▼";
  };

  const handleRowClick = (meterId: string) => {
    navigate(`/meters/${meterId}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent, meterId: string) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleRowClick(meterId);
    }
  };

  if (meters.length === 0) {
    return <div className={styles.empty}>Sin resultados para el filtro seleccionado.</div>;
  }

  return (
    <div className={styles.tableWrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th className={styles.th}>
              <button type="button" className={styles.sortButton} onClick={() => handleSort("name")}>
                Nombre{getSortIcon("name")}
              </button>
            </th>
            <th className={styles.th}>
              <button type="button" className={styles.sortButton} onClick={() => handleSort("status")}>
                Estado{getSortIcon("status")}
              </button>
            </th>
            <th className={styles.th}>
              <button type="button" className={styles.sortButton} onClick={() => handleSort("consumption_kwh")}>
                Consumo{getSortIcon("consumption_kwh")}
              </button>
            </th>
            <th className={styles.th}>
              <button type="button" className={styles.sortButton} onClick={() => handleSort("variation_pct")}>
                Variación{getSortIcon("variation_pct")}
              </button>
            </th>
            <th className={styles.th}>
              <button type="button" className={styles.sortButton} onClick={() => handleSort("anomaly_severity")}>
                Severidad{getSortIcon("anomaly_severity")}
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedMeters.map((meter) => {
            const hasHighVariation = meter.variation_pct !== null && Math.abs(meter.variation_pct) > 30;
            return (
              <tr 
                key={meter.meter_id} 
                className={styles.row}
                onClick={() => handleRowClick(meter.meter_id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => handleKeyDown(e, meter.meter_id)}
              >
                <td className={styles.td} data-label="Nombre">{meter.name}</td>
                <td className={styles.td} data-label="Estado">
                  <Badge label={meter.status} tone={meterStatusToColorToken(meter.status)} />
                </td>
                <td className={styles.td} data-label="Consumo">{formatKwh(meter.consumption_kwh)}</td>
                <td className={styles.td} data-label="Variación">
                  {meter.variation_pct !== null ? (
                    hasHighVariation ? (
                      <Badge 
                        label={formatVariationPct(meter.variation_pct)} 
                        tone="critical" 
                      />
                    ) : (
                      formatVariationPct(meter.variation_pct)
                    )
                  ) : (
                    "—"
                  )}
                </td>
                <td className={styles.td} data-label="Severidad">
                  {meter.anomaly_severity !== null ? (
                    <Badge 
                      label={meter.anomaly_severity} 
                      tone={severityToColorToken(meter.anomaly_severity)} 
                    />
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
