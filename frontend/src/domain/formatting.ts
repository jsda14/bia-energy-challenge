/** Formatea un valor en kWh con 1 decimal y sufijo, ej. "1,234.5 kWh". */
export function formatKwh(value: number): string {
  return `${new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value)} kWh`;
}

/** Formatea una variación porcentual con signo, ej. "+78.9%" o "-12.3%". */
export function formatVariationPct(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value)}%`;
}

/** Formatea un ISO datetime string a fecha/hora legible en es-ES, ej. "24 sep 2026, 14:00". */
export function formatDateTime(isoString: string): string {
  const date = new Date(isoString);
  return new Intl.DateTimeFormat("es-ES", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

/** Mapea un severity string del backend ("LOW"|"MEDIUM"|"HIGH") a un token de color semántico ("neutral"|"warning"|"critical"). Cualquier valor no reconocido retorna "neutral" (fallback seguro, nunca lanza). */
export function severityToColorToken(severity: string): "neutral" | "warning" | "critical" {
  switch (severity) {
    case "LOW":
      return "neutral";
    case "MEDIUM":
      return "warning";
    case "HIGH":
      return "critical";
    default:
      return "neutral";
  }
}

/** Mapea un meter status string ("OK"|"Alert"|"Critical") a un token de color semántico, mismo criterio de fallback que severityToColorToken. */
export function meterStatusToColorToken(status: string): "neutral" | "warning" | "critical" {
  switch (status) {
    case "Alert":
      return "warning";
    case "Critical":
      return "critical";
    case "OK":
    default:
      return "neutral";
  }
}

/** Mapea un triage_status string ("NEW"|"ACKNOWLEDGED"|"DISMISSED") a un token de color semántico. Cualquier valor no reconocido retorna "neutral" (fallback seguro, nunca lanza), mismo criterio que severityToColorToken. */
export function triageStatusToColorToken(status: string): "neutral" | "warning" | "critical" {
  switch (status) {
    case "ACKNOWLEDGED":
      return "warning";
    case "NEW":
    case "DISMISSED":
    default:
      return "neutral";
  }
}

/** Mapea un triage_status string ("NEW"|"ACKNOWLEDGED"|"DISMISSED") a su
 * etiqueta en español — mismo mapeo que TriageStatusBadge, extraído acá
 * para reutilizarlo también en AnomaliesFilterBar sin duplicar la lógica
 * de traducción en dos lugares. Cualquier valor no reconocido cae a
 * "Nueva" (fallback silencioso, mismo criterio que severityToColorToken). */
export function triageStatusToLabel(status: string): string {
  switch (status) {
    case "ACKNOWLEDGED":
      return "Atendida";
    case "DISMISSED":
      return "Descartada";
    case "NEW":
    default:
      return "Nueva";
  }
}
