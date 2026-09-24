from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class AnalysisRunStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisRun(BaseModel):
    """Registro inmutable de una ejecución de análisis de anomalías.

    Attributes:
        id: Identificador único de la ejecución (UUID como string).
        requested_meter_id: meter_id específico solicitado, o None si fue
            "analizar todos los medidores".
        status: Estado final de la ejecución.
        started_at: Momento en que se inició el análisis.
        finished_at: Momento en que terminó el análisis.
        anomalies_detected_count: Cantidad total de AnomalyRecord generados.
        error_message: Detalle del error si status es FAILED, None si
            status es COMPLETED.
    """

    model_config = {"frozen": True}

    id: str
    requested_meter_id: str | None
    status: AnalysisRunStatus
    started_at: datetime
    finished_at: datetime
    anomalies_detected_count: int
    error_message: str | None = None
