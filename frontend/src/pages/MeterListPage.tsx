import { useState, useMemo } from "react";
import { useMeters } from "../api/queries/useMeters";
import { MetersTable } from "../components/feature/MetersTable";
import { MetersFilterBar } from "../components/feature/MetersFilterBar";
import styles from "./MeterListPage.module.css";

export default function MeterListPage() {
  const { data: meters, isLoading, isError } = useMeters();
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string | null>(null);

  const statusOptions = useMemo(() => {
    if (!meters) return [];
    return Array.from(new Set(meters.map((m) => m.status)));
  }, [meters]);

  const severityOptions = useMemo(() => {
    if (!meters) return [];
    return Array.from(new Set(meters.map((m) => m.anomaly_severity).filter((s): s is string => s !== null)));
  }, [meters]);

  const filteredMeters = useMemo(() => {
    if (!meters) return [];
    return meters.filter((meter) => {
      if (selectedStatus && meter.status !== selectedStatus) return false;
      if (selectedSeverity && meter.anomaly_severity !== selectedSeverity) return false;
      return true;
    });
  }, [meters, selectedStatus, selectedSeverity]);

  if (isLoading) {
    return <div>Cargando...</div>;
  }

  if (isError) {
    return <div>Error al cargar la lista de medidores.</div>;
  }

  if (!meters || meters.length === 0) {
    return <div>No hay medidores registrados.</div>;
  }

  return (
    <div className={styles["meter-list"]}>
      <h1 className={styles["meter-list__title"]}>Medidores</h1>
      
      <MetersFilterBar
        statusOptions={statusOptions}
        severityOptions={severityOptions}
        selectedStatus={selectedStatus}
        selectedSeverity={selectedSeverity}
        onStatusChange={setSelectedStatus}
        onSeverityChange={setSelectedSeverity}
      />
      
      <MetersTable meters={filteredMeters} />
    </div>
  );
}
