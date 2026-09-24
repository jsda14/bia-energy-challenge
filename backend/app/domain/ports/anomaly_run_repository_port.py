from typing import Protocol
from app.domain.models.anomaly_run import AnalysisRun


class AnomalyRunRepositoryPort(Protocol):
    """Puerto para persistir y consultar ejecuciones de análisis."""

    def save(self, run: AnalysisRun) -> None:
        """Persiste una ejecución de análisis. run.id ya viene asignado por
        el caller (el caso de uso genera el UUID antes de llamar save)."""
        ...

    def get_by_id(self, run_id: str) -> AnalysisRun | None:
        """Retorna la ejecución cuyo id coincide, o None si no existe."""
        ...
