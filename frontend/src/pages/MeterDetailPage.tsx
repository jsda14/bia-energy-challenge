import { useParams } from "react-router-dom";
import { useMeterDetail } from "../api/queries/useMeterDetail";
import { DetailField } from "../components/ui/DetailField";
import { Badge } from "../components/ui/Badge";
import { Breadcrumb } from "../components/ui/Breadcrumb";
import { MeterHistoryChart } from "../components/feature/MeterHistoryChart";
import { formatKwh, formatVariationPct, meterStatusToColorToken } from "../domain/formatting";
import styles from "./MeterDetailPage.module.css";

export default function MeterDetailPage() {
  const { meterId } = useParams<{ meterId: string }>();
  const { data: meter, isLoading, isError } = useMeterDetail(meterId || "");

  if (isLoading) {
    return <div>Cargando...</div>;
  }

  if (isError || !meter) {
    return <div>Error al cargar el detalle del medidor.</div>;
  }

  return (
    <div className={styles.container}>
      <Breadcrumb
        items={[
          { label: "Medidores", to: "/meters" },
          { label: meter.name },
        ]}
      />
      <div className={styles.header}>
        <h1 className={styles.header__title}>Detalle de Medidor</h1>
      </div>
      
      <div className={styles.detailGrid}>
        <DetailField label="ID Medidor" value={meter.meter_id} />
        <DetailField label="Nombre" value={meter.name} />
        <DetailField label="Ubicación" value={meter.location} />
        <div className={styles.fieldWrapper}>
          <span className={styles.label}>Estado</span>
          <Badge label={meter.status} tone={meterStatusToColorToken(meter.status)} />
        </div>
        <DetailField label="Consumo actual" value={formatKwh(meter.consumption_kwh)} />
        <DetailField 
          label="Baseline" 
          value={meter.baseline_kwh !== null ? formatKwh(meter.baseline_kwh) : "—"} 
        />
        <DetailField 
          label="Variación" 
          value={meter.variation_pct !== null ? formatVariationPct(meter.variation_pct) : "—"} 
          tone={meter.variation_pct !== null && Math.abs(meter.variation_pct) > 30 ? "critical" : "neutral"}
        />
      </div>

      <h2 className={styles.subtitle}>Historial de Lecturas</h2>
      <MeterHistoryChart readings={meter.readings} baselineKwh={meter.baseline_kwh} />
    </div>
  );
}
