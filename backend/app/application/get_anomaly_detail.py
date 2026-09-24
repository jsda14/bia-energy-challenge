from app.application.dtos import AnomalyDetailDTO
from app.domain.ports.anomaly_repository_port import AnomalyRepositoryPort

class GetAnomalyDetailUseCase:
    def __init__(self, anomaly_repo: AnomalyRepositoryPort) -> None:
        self.anomaly_repo = anomaly_repo

    def execute(self, anomaly_id: str) -> AnomalyDetailDTO | None:
        a = self.anomaly_repo.get_by_id(anomaly_id)
        if not a:
            return None
            
        ev = a.record.evidence
        return AnomalyDetailDTO(
            id=a.id,
            meter_id=a.record.meter_id,
            type=a.record.type.value,
            severity=a.record.severity.value,
            confidence=a.record.confidence,
            reason=a.reason,
            recommended_action=a.recommended_action,
            baseline_kwh=ev.baseline_kwh,
            observed_kwh=ev.observed_kwh,
            variation_pct=ev.variation_pct,
            affected_variables=ev.affected_variables,
            correlated_event=ev.correlated_event,
            window_start=ev.window_start,
            window_end=ev.window_end,
        )
