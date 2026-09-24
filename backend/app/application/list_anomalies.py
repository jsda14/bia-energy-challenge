from app.application.dtos import AnomalySummaryDTO
from app.domain.ports.anomaly_repository_port import AnomalyRepositoryPort

class ListAnomaliesUseCase:
    def __init__(self, anomaly_repo: AnomalyRepositoryPort) -> None:
        self.anomaly_repo = anomaly_repo

    def execute(self, meter_id: str | None = None) -> list[AnomalySummaryDTO]:
        if meter_id:
            anomalies = self.anomaly_repo.get_by_meter_id(meter_id)
        else:
            anomalies = self.anomaly_repo.get_all()
            
        return [
            AnomalySummaryDTO(
                id=a.id,
                meter_id=a.record.meter_id,
                type=a.record.type.value,
                severity=a.record.severity.value,
                confidence=a.record.confidence,
                recommended_action=a.recommended_action,
                detected_at=a.record.detected_at,
            )
            for a in anomalies
        ]
