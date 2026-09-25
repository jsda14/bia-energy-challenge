import { useState, useMemo } from "react";
import { useAnomalies } from "../api/queries/useAnomalies";
import { AnomaliesTable } from "../components/feature/AnomaliesTable";
import { AnomaliesFilterBar } from "../components/feature/AnomaliesFilterBar";
import styles from "./AnomaliesPage.module.css";

export default function AnomaliesPage() {
  const { data: anomalies, isLoading, isError } = useAnomalies();
  const [selectedMeterId, setSelectedMeterId] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string | null>(null);

  const meterIdOptions = useMemo(() => {
    if (!anomalies) return [];
    return Array.from(new Set(anomalies.map((a) => a.meter_id)));
  }, [anomalies]);

  const typeOptions = useMemo(() => {
    if (!anomalies) return [];
    return Array.from(new Set(anomalies.map((a) => a.type)));
  }, [anomalies]);

  const severityOptions = useMemo(() => {
    if (!anomalies) return [];
    return Array.from(new Set(anomalies.map((a) => a.severity)));
  }, [anomalies]);

  const filteredAnomalies = useMemo(() => {
    if (!anomalies) return [];
    return anomalies.filter((anomaly) => {
      if (selectedMeterId && anomaly.meter_id !== selectedMeterId) return false;
      if (selectedType && anomaly.type !== selectedType) return false;
      if (selectedSeverity && anomaly.severity !== selectedSeverity) return false;
      return true;
    });
  }, [anomalies, selectedMeterId, selectedType, selectedSeverity]);

  if (isLoading) {
    return <div>Cargando...</div>;
  }

  if (isError) {
    return <div>Error al cargar la lista de anomalías.</div>;
  }

  if (!anomalies || anomalies.length === 0) {
    return <div>No hay anomalías detectadas.</div>;
  }

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Anomalías</h1>
      <AnomaliesFilterBar
        meterIdOptions={meterIdOptions}
        typeOptions={typeOptions}
        severityOptions={severityOptions}
        selectedMeterId={selectedMeterId}
        selectedType={selectedType}
        selectedSeverity={selectedSeverity}
        onMeterIdChange={setSelectedMeterId}
        onTypeChange={setSelectedType}
        onSeverityChange={setSelectedSeverity}
      />
      <AnomaliesTable anomalies={filteredAnomalies} />
    </div>
  );
}
