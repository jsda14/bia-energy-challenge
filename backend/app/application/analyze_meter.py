import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from app.domain.models.anomaly_run import AnalysisRun, AnalysisRunStatus
from app.domain.ports.ai_explainer_port import AIExplainerPort
from app.domain.ports.anomaly_repository_port import AnomalyRepositoryPort
from app.domain.ports.anomaly_run_repository_port import AnomalyRunRepositoryPort
from app.domain.ports.event_repository_port import EventRepositoryPort
from app.domain.ports.meter_repository_port import MeterRepositoryPort
from app.domain.ports.reading_repository_port import ReadingRepositoryPort
from app.domain.detection.detector import AnomalyDetector

class AnalyzeMeterUseCase:
    """Orquesta un ciclo completo de análisis."""

    def __init__(
        self,
        meter_repo: MeterRepositoryPort,
        reading_repo: ReadingRepositoryPort,
        event_repo: EventRepositoryPort,
        anomaly_repo: AnomalyRepositoryPort,
        run_repo: AnomalyRunRepositoryPort,
        explainer: AIExplainerPort,
        detector: AnomalyDetector,
    ) -> None:
        self.meter_repo = meter_repo
        self.reading_repo = reading_repo
        self.event_repo = event_repo
        self.anomaly_repo = anomaly_repo
        self.run_repo = run_repo
        self.explainer = explainer
        self.detector = detector

    def execute(self, meter_id: str | None = None) -> AnalysisRun:
        started_at = datetime.utcnow()
        
        if meter_id is not None:
            m = self.meter_repo.get_by_meter_id(meter_id)
            if not m:
                run = AnalysisRun(
                    id=str(uuid.uuid4()),
                    requested_meter_id=meter_id,
                    status=AnalysisRunStatus.FAILED,
                    started_at=started_at,
                    finished_at=datetime.utcnow(),
                    anomalies_detected_count=0,
                    error_message=f"Meter '{meter_id}' not found",
                )
                self.run_repo.save(run)
                return run
            meters_to_analyze = [m]
        else:
            meters_to_analyze = self.meter_repo.get_all()
            
        total_anomalies = 0
        error_msg = None
        
        for m in meters_to_analyze:
            try:
                readings = self.reading_repo.get_by_meter_id(m.meter_id)
                events = self.event_repo.get_by_meter_id(m.meter_id)
                
                anomalies = self.detector.analyze(m.meter_id, readings, events, started_at)
                if anomalies:
                    items_to_save = []
                    for anomaly in anomalies:
                        explanation = self.explainer.explain(anomaly)
                        items_to_save.append((anomaly, explanation))
                    self.anomaly_repo.save_many(items_to_save)
                    total_anomalies += len(anomalies)
            except Exception as e:
                logger.warning(f"Exception analyzing meter {m.meter_id}: {e}")
                # Si es para todos, atrapamos para no tumbar el análisis completo
                if meter_id is None:
                    continue
                else:
                    error_msg = str(e)
                    run = AnalysisRun(
                        id=str(uuid.uuid4()),
                        requested_meter_id=meter_id,
                        status=AnalysisRunStatus.FAILED,
                        started_at=started_at,
                        finished_at=datetime.utcnow(),
                        anomalies_detected_count=total_anomalies,
                        error_message=error_msg,
                    )
                    self.run_repo.save(run)
                    return run
                    
        run = AnalysisRun(
            id=str(uuid.uuid4()),
            requested_meter_id=meter_id,
            status=AnalysisRunStatus.COMPLETED,
            started_at=started_at,
            finished_at=datetime.utcnow(),
            anomalies_detected_count=total_anomalies,
            error_message=None,
        )
        self.run_repo.save(run)
        return run
