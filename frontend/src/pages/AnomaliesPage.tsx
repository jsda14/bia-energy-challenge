import { useAnomalies } from "../api/queries/useAnomalies";
import { AnomaliesTable } from "../components/feature/AnomaliesTable";
import styles from "./AnomaliesPage.module.css";

export default function AnomaliesPage() {
  const { data: anomalies, isLoading, isError } = useAnomalies();

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
      <AnomaliesTable anomalies={anomalies} />
    </div>
  );
}
