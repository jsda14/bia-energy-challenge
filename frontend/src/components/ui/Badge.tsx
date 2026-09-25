import styles from "./Badge.module.css";

interface BadgeProps {
  label: string;
  tone: "neutral" | "warning" | "critical";
}

export function Badge({ label, tone }: BadgeProps) {
  return (
    <span className={`${styles.badge} ${styles[`badge--${tone}`]}`}>
      {label}
    </span>
  );
}
