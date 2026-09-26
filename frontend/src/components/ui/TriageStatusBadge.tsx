import { triageStatusToLabel } from "../../domain/formatting";
import styles from "./TriageStatusBadge.module.css";

interface TriageStatusBadgeProps {
  status: string;
}

export function TriageStatusBadge({ status }: TriageStatusBadgeProps) {
  if (status === "ACKNOWLEDGED") {
    return <span className={`${styles.badge} ${styles["badge--acknowledged"]}`}>{triageStatusToLabel(status)}</span>;
  }

  if (status === "DISMISSED") {
    return <span className={`${styles.badge} ${styles["badge--dismissed"]}`}>{triageStatusToLabel(status)}</span>;
  }

  // "NEW" y cualquier valor no reconocido caen acá (fallback silencioso,
  // mismo criterio que severityToColorToken/SourceBadge).
  return <span className={`${styles.badge} ${styles["badge--new"]}`}>{triageStatusToLabel(status)}</span>;
}
