from app.application.dtos import MeterSummaryDTO
from app.domain.ports.meter_repository_port import MeterRepositoryPort
from app.domain.ports.reading_repository_port import ReadingRepositoryPort
from app.domain.ports.anomaly_repository_port import AnomalyRepositoryPort

class ListMetersUseCase:
    def __init__(
        self,
        meter_repo: MeterRepositoryPort,
        reading_repo: ReadingRepositoryPort,
        anomaly_repo: AnomalyRepositoryPort,
    ) -> None:
        self.meter_repo = meter_repo
        self.reading_repo = reading_repo
        self.anomaly_repo = anomaly_repo

    def execute(self) -> list[MeterSummaryDTO]:
        meters = self.meter_repo.get_all()
        result = []
        for m in meters:
            readings = self.reading_repo.get_by_meter_id(m.meter_id)
            anomalies = self.anomaly_repo.get_by_meter_id(m.meter_id)
            
            consumption_kwh = sum(r.consumption_kwh for r in readings) if readings else 0.0
            
            status = "OK"
            if any(a.record.severity.value == "HIGH" for a in anomalies):
                status = "Critical"
            elif any(a.record.severity.value == "MEDIUM" for a in anomalies):
                status = "Alert"
                
            anomaly_severity = None
            if anomalies:
                anomaly_severity = anomalies[0].record.severity.value
                
            variation_pct = None
            if anomalies:
                variation_pct = anomalies[0].record.evidence.variation_pct
            
            result.append(MeterSummaryDTO(
                meter_id=m.meter_id,
                name=m.name,
                status=status,
                consumption_kwh=consumption_kwh,
                variation_pct=variation_pct,
                anomaly_severity=anomaly_severity,
            ))
            
        return result
