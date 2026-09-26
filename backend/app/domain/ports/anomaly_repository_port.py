from datetime import datetime
from typing import Protocol
from app.domain.models.anomaly import AnomalyRecord, PersistedAnomaly
from app.domain.ports.ai_explainer_port import AIExplanation


class AnomalyRepositoryPort(Protocol):
    """Puerto para persistir y consultar anomalías detectadas."""

    def exists(self, meter_id: str, anomaly_type: str, window_start: datetime, window_end: datetime) -> bool:
        """Retorna True si ya existe una anomalía persistida con esta
        combinación exacta (meter_id, type, window_start, window_end) —
        la misma clave natural de idempotencia que usa `save_many`. Permite
        al caller (AnalyzeMeterUseCase) evitar pedirle una explicación al
        AIExplainerPort (posiblemente una llamada real y costosa a Claude)
        para una anomalía que de todos modos no se va a insertar de nuevo."""
        ...

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

    def update_explanation(self, anomaly_id: str, explanation: AIExplanation) -> bool:
        """Actualiza únicamente `reason`/`recommended_action` de una anomalía
        ya persistida, sin tocar ningún otro campo (type/severity/confidence/
        evidence/detected_at permanecen intactos — esto NO es una nueva
        detección, es solo una nueva explicación en lenguaje natural sobre
        el mismo incidente ya detectado). Retorna True si la anomalía existía
        y se actualizó, False si `anomaly_id` no existe."""
        ...

    def update_triage_status(self, anomaly_id: str, triage_status: str) -> bool:
        """Actualiza únicamente `triage_status` de una anomalía ya
        persistida, sin tocar ningún otro campo. Reversible en cualquier
        dirección, sin restricción de transición (SPEC-013). Retorna True
        si la anomalía existía y se actualizó, False si `anomaly_id` no
        existe (mismo contrato de retorno que `update_explanation`)."""
        ...
