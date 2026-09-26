from app.application.dtos import AnomalyDetailDTO
from app.domain.ports.anomaly_repository_port import AnomalyRepositoryPort


class UpdateAnomalyTriageStatusUseCase:
    """Actualiza el estado de triage (NEW/ACKNOWLEDGED/DISMISSED) de una
    anomalía ya persistida, sin tocar ningún otro campo. Reversible sin
    restricción de transición (SPEC-013) — no hay noción de "quién" lo
    cambió, el MVP no tiene autenticación (confirmado desde SPEC-003).
    """

    def __init__(self, anomaly_repo: AnomalyRepositoryPort) -> None:
        self.anomaly_repo = anomaly_repo

    def execute(self, anomaly_id: str, triage_status: str) -> AnomalyDetailDTO | None:
        persisted = self.anomaly_repo.get_by_id(anomaly_id)
        if not persisted:
            return None

        self.anomaly_repo.update_triage_status(anomaly_id, triage_status)

        ev = persisted.record.evidence
        return AnomalyDetailDTO(
            id=persisted.id,
            meter_id=persisted.record.meter_id,
            type=persisted.record.type.value,
            severity=persisted.record.severity.value,
            confidence=persisted.record.confidence,
            reason=persisted.reason,
            recommended_action=persisted.recommended_action,
            explanation_source=persisted.explanation_source,
            triage_status=triage_status,
            baseline_kwh=ev.baseline_kwh,
            observed_kwh=ev.observed_kwh,
            variation_pct=ev.variation_pct,
            affected_variables=ev.affected_variables,
            correlated_event=ev.correlated_event,
            window_start=ev.window_start,
            window_end=ev.window_end,
        )
