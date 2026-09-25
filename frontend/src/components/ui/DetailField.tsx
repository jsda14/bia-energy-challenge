import styles from "./DetailField.module.css";

interface DetailFieldProps {
  label: string;
  value: string;
  tone?: "neutral" | "warning" | "critical";
}

export function DetailField({ label, value, tone = "neutral" }: DetailFieldProps) {
  return (
    <div className={`${styles.detailField} ${styles[`detailField--${tone}`]}`}>
      <span className={styles.label}>{label}</span>
      <span className={styles.value}>{value}</span>
    </div>
  );
}
