import { useState, useMemo } from "react";
import { useMeters } from "../api/queries/useMeters";
import { MetersTable } from "../components/feature/MetersTable";
import { MetersFilterBar } from "../components/feature/MetersFilterBar";
import { Skeleton } from "../components/ui/Skeleton";
import styles from "./MeterListPage.module.css";

function MeterListSkeleton() {
  return (
    <div className={styles["meter-list-page__meter-list"]}>
      <Skeleton width="160px" height="2rem" className={styles["meter-list-page__title"]} />
      <Skeleton height="44px" />
      <div className={styles["meter-list-page__skeleton-rows"]}>
        <Skeleton height="88px" />
        <Skeleton height="88px" />
        <Skeleton height="88px" />
        <Skeleton height="88px" />
      </div>
    </div>
  );
}

export default function MeterListPage() {
  const { data: meters, isLoading, isError } = useMeters();
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

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
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        if (
          !meter.meter_id.toLowerCase().includes(query) &&
          !meter.name.toLowerCase().includes(query)
        ) {
          return false;
        }
      }
      return true;
    });
  }, [meters, selectedStatus, selectedSeverity, searchQuery]);

  if (isLoading) {
    return <MeterListSkeleton />;
  }

  if (isError) {
    return <div>Error al cargar la lista de medidores.</div>;
  }

  if (!meters || meters.length === 0) {
    return <div>No hay medidores registrados.</div>;
  }

  return (
    <div className={styles["meter-list-page__meter-list"]}>
      <h1 className={styles["meter-list-page__title"]}>Medidores</h1>
      
      <MetersFilterBar
        statusOptions={statusOptions}
        severityOptions={severityOptions}
        selectedStatus={selectedStatus}
        selectedSeverity={selectedSeverity}
        searchQuery={searchQuery}
        onStatusChange={setSelectedStatus}
        onSeverityChange={setSelectedSeverity}
        onSearchChange={setSearchQuery}
      />
      
      <MetersTable meters={filteredMeters} />
    </div>
  );
}
