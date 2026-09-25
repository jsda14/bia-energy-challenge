import { useParams } from "react-router-dom";
import { useAnomalyDetail } from "../api/queries/useAnomalyDetail";
import { useMeterDetail } from "../api/queries/useMeterDetail";
import { DetailField } from "../components/ui/DetailField";
import { Badge } from "../components/ui/Badge";
import { Breadcrumb } from "../components/ui/Breadcrumb";
import { RunAnalysisButton } from "../components/ui/RunAnalysisButton";
import { MeterHistoryChart } from "../components/feature/MeterHistoryChart";
import { formatDateTime, severityToColorToken, formatVariationPct } from "../domain/formatting";
import styles from "./AnomalyDetailPage.module.css";

export default function AnomalyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: anomaly, isLoading, isError } = useAnomalyDetail(id || "");
  const { data: meter, isLoading: isMeterLoading, isError: isMeterError } = useMeterDetail(anomaly?.meter_id ?? "");

  if (isLoading) {
    return <div>Cargando...</div>;
  }

  if (isError || !anomaly) {
    return <div>Error al cargar el detalle de la anomalía.</div>;
  }

  return (
    <div className={styles.container}>
      <Breadcrumb
        items={[
          { label: "Anomalías", to: "/anomalies" },
          { label: anomaly.type },
        ]}
      />
      <div className={styles.header}>
        <h1 className={styles.header__title}>Detalle de Anomalía</h1>
        <RunAnalysisButton meterId={anomaly.meter_id} />
      </div>
      
      <div className={styles.detailGrid}>
        <DetailField label="Medidor" value={anomaly.meter_id} />
        <DetailField label="Tipo" value={anomaly.type} />
        <div className={styles.fieldWrapper}>
          <span className={styles.label}>Severidad</span>
          <Badge label={anomaly.severity} tone={severityToColorToken(anomaly.severity)} />
        </div>
        <DetailField label="Confianza" value={`${(anomaly.confidence * 100).toFixed(0)}%`} />
        
        <DetailField label="Baseline" value={anomaly.baseline_kwh.toString()} />
        <DetailField label="Observado" value={anomaly.observed_kwh.toString()} />
        <DetailField 
          label="Variación" 
          value={formatVariationPct(anomaly.variation_pct)} 
          tone={Math.abs(anomaly.variation_pct) > 30 ? "critical" : "neutral"}
        />
        
        <DetailField 
          label="Variables Afectadas" 
          value={anomaly.affected_variables.length > 0 ? anomaly.affected_variables.join(", ") : "—"} 
        />
        
        <DetailField 
          label="Evento Correlacionado" 
          value={anomaly.correlated_event !== null ? anomaly.correlated_event : "Sin evento correlacionado"} 
        />
        
        <DetailField 
          label="Ventana de Detección" 
          value={`${formatDateTime(anomaly.window_start)} – ${formatDateTime(anomaly.window_end)}`} 
        />
      </div>

      <div className={styles.textSection}>
        <h2 className={styles.subtitle}>Evidencia Visual</h2>
        {isMeterLoading ? (
          <div>Cargando evidencia visual…</div>
        ) : isMeterError || !meter ? (
          <div>Error al cargar la evidencia visual.</div>
        ) : (
          <MeterHistoryChart 
            readings={meter.readings} 
            baselineKwh={meter.baseline_kwh}
            highlightStart={anomaly.window_start}
            highlightEnd={anomaly.window_end}
          />
        )}
      </div>

      <div className={styles.textSection}>
        <h2 className={styles.subtitle}>Razón</h2>
        <p className={styles.text}>{anomaly.reason}</p>
      </div>

      <div className={styles.textSection}>
        <h2 className={styles.subtitle}>Acción Recomendada</h2>
        <p className={styles.text}>{anomaly.recommended_action}</p>
      </div>
    </div>
  );
}
