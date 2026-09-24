"""Puerto y contratos para el componente de explicación con IA."""

from typing import Protocol
from pydantic import BaseModel
from app.domain.models.anomaly import AnomalyRecord


class AIExplanation(BaseModel):
    """Explicación y recomendación en lenguaje natural para una anomalía.

    Attributes:
        reason: Justificación o diagnóstico narrativo de la causa de la anomalía.
        recommended_action: Acción sugerida u operativa para resolver o mitigar la anomalía.
    """

    reason: str
    recommended_action: str


class AIExplainerPort(Protocol):
    """Puerto que define la interfaz para generar explicaciones con modelos de lenguaje."""

    def explain(self, anomaly: AnomalyRecord) -> AIExplanation:
        """Genera explicación y recomendación en lenguaje natural para una anomalía.

        Args:
            anomaly: Registro de anomalía clasificada por el motor de dominio.

        Returns:
            AIExplanation con razón y acción recomendada en lenguaje natural.
        """
        ...
