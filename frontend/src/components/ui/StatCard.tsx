import styles from "./StatCard.module.css";

interface StatCardProps {
  label: string;
  /** Ya formateado por el caller (ej. formatKwh, o un número plano con "—" si es null). */
  value: string;
  /** Tono opcional para dar énfasis visual (ej. tarjeta de alta prioridad en "warning"). */
  tone?: "neutral" | "warning" | "critical";
}

export function StatCard({ label, value, tone = "neutral" }: StatCardProps) {
  return (
    <div className={`${styles["stat-card"]} ${styles[`stat-card--${tone}`]}`}>
      <span className={styles["stat-card__label"]}>{label}</span>
      <span className={styles["stat-card__value"]}>{value}</span>
    </div>
  );
}
