import styles from "./SourceBadge.module.css";

interface SourceBadgeProps {
  source: string;
}

export function SourceBadge({ source }: SourceBadgeProps) {
  if (source === "ai") {
    return <span className={`${styles["source-badge"]} ${styles["source-badge--ai"]}`}>Generado por IA</span>;
  }
  
  return <span className={`${styles["source-badge"]} ${styles["source-badge--template"]}`}>Plantilla predefinida</span>;
}
