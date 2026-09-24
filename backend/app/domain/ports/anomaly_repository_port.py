from typing import Protocol
from app.domain.models.anomaly import AnomalyRecord, PersistedAnomaly
from app.domain.ports.ai_explainer_port import AIExplanation


class AnomalyRepositoryPort(Protocol):
    """Puerto para persistir y consultar anomalías detectadas."""

    def get_all(self) -> list[PersistedAnomaly]:
        """Retorna todas las anomalías persistidas, sin filtros, ordenadas
        por record.detected_at descendente (más reciente primero).
        """
        ...

    def get_by_id(self, anomaly_id: str) -> PersistedAnomaly | None:
        """Retorna la anomalía cuyo id coincide, o None si no existe."""
        ...

    def get_by_meter_id(self, meter_id: str) -> list[PersistedAnomaly]:
        """Retorna las anomalías de un medidor, ordenadas por record.detected_at descendente."""
        ...

    def save_many(self, items: list[tuple[AnomalyRecord, AIExplanation]]) -> list[str]:
        """Persiste múltiples registros de anomalía junto con sus explicaciones.
        
        Genera los IDs (UUIDv4) para cada anomalía y los retorna.
        """
        ...
