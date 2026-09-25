import styles from "./SourceBadge.module.css";

interface SourceBadgeProps {
  source: string;
}

export function SourceBadge({ source }: SourceBadgeProps) {
  if (source === "ai") {
    return <span className={`${styles.badge} ${styles["badge--ai"]}`}>Generado por IA</span>;
  }
  
  return <span className={`${styles.badge} ${styles["badge--template"]}`}>Plantilla predefinida</span>;
}
