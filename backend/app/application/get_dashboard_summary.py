from app.application.dtos import DashboardSummaryDTO
from app.domain.ports.anomaly_repository_port import AnomalyRepositoryPort
from app.domain.ports.anomaly_run_repository_port import AnomalyRunRepositoryPort
from app.domain.ports.meter_repository_port import MeterRepositoryPort

class GetDashboardSummaryUseCase:
    def __init__(
        self,
        meter_repo: MeterRepositoryPort,
        anomaly_repo: AnomalyRepositoryPort,
        run_repo: AnomalyRunRepositoryPort,
    ) -> None:
        self.meter_repo = meter_repo
        self.anomaly_repo = anomaly_repo
        self.run_repo = run_repo

    def execute(self) -> DashboardSummaryDTO:
        anomalies = self.anomaly_repo.get_all()
        latest_run = self.run_repo.get_latest()
        last_analysis = latest_run.finished_at if latest_run else None

        if not anomalies:
            return DashboardSummaryDTO(
                anomalies_detected=0,
                high_priority_count=0,
                average_confidence=None,
                last_analysis_at=last_analysis,
            )

        anomalies_detected = len(anomalies)
        high_priority = sum(1 for a in anomalies if a.record.severity.value == "HIGH")
        avg_confidence = sum(a.record.confidence for a in anomalies) / anomalies_detected

        return DashboardSummaryDTO(
            anomalies_detected=anomalies_detected,
            high_priority_count=high_priority,
            average_confidence=avg_confidence,
            last_analysis_at=last_analysis,
        )
