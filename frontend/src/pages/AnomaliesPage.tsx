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
  const [selectedTriageStatus, setSelectedTriageStatus] = useState<string | null>(null);

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

  const triageStatusOptions = useMemo(() => {
    if (!anomalies) return [];
    return Array.from(new Set(anomalies.map((a) => a.triage_status)));
  }, [anomalies]);

  const filteredAnomalies = useMemo(() => {
    if (!anomalies) return [];
    return anomalies.filter((anomaly) => {
      if (selectedMeterId && anomaly.meter_id !== selectedMeterId) return false;
      if (selectedType && anomaly.type !== selectedType) return false;
      if (selectedSeverity && anomaly.severity !== selectedSeverity) return false;
      // "Todas" (null) es el default — nunca oculta DISMISSED por defecto,
      // solo cuando el usuario elige explícitamente un estado (SPEC-013).
      if (selectedTriageStatus && anomaly.triage_status !== selectedTriageStatus) return false;
      return true;
    });
  }, [anomalies, selectedMeterId, selectedType, selectedSeverity, selectedTriageStatus]);

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
        triageStatusOptions={triageStatusOptions}
        selectedMeterId={selectedMeterId}
        selectedType={selectedType}
        selectedSeverity={selectedSeverity}
        selectedTriageStatus={selectedTriageStatus}
        onMeterIdChange={setSelectedMeterId}
        onTypeChange={setSelectedType}
        onSeverityChange={setSelectedSeverity}
        onTriageStatusChange={setSelectedTriageStatus}
      />
      <AnomaliesTable anomalies={filteredAnomalies} />
    </div>
  );
}
