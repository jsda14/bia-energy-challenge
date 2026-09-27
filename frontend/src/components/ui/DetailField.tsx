import styles from "./DetailField.module.css";

interface DetailFieldProps {
  label: string;
  value: string;
  tone?: "neutral" | "warning" | "critical";
}

export function DetailField({ label, value, tone = "neutral" }: DetailFieldProps) {
  return (
    <div className={`${styles["detail-field"]} ${styles[`detail-field--${tone}`]}`}>
      <span className={styles["detail-field__label"]}>{label}</span>
      <span className={styles["detail-field__value"]}>{value}</span>
    </div>
  );
}
