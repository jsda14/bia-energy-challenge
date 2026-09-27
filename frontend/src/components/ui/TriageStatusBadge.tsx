import { triageStatusToLabel } from "../../domain/formatting";
import styles from "./TriageStatusBadge.module.css";

interface TriageStatusBadgeProps {
  status: string;
}

export function TriageStatusBadge({ status }: TriageStatusBadgeProps) {
  if (status === "ACKNOWLEDGED") {
    return <span className={`${styles["triage-status-badge"]} ${styles["triage-status-badge--acknowledged"]}`}>{triageStatusToLabel(status)}</span>;
  }

  if (status === "DISMISSED") {
    return <span className={`${styles["triage-status-badge"]} ${styles["triage-status-badge--dismissed"]}`}>{triageStatusToLabel(status)}</span>;
  }

  // "NEW" y cualquier valor no reconocido caen acá (fallback silencioso,
  // mismo criterio que severityToColorToken/SourceBadge).
  return <span className={`${styles["triage-status-badge"]} ${styles["triage-status-badge--new"]}`}>{triageStatusToLabel(status)}</span>;
}
