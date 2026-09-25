"""Puerto y contratos para el componente de explicación con IA."""

from typing import Literal, Protocol
from pydantic import BaseModel
from app.domain.models.anomaly import AnomalyRecord


class AIExplanation(BaseModel):
    """Explicación y recomendación en lenguaje natural para una anomalía.

    Attributes:
        reason: Justificación o diagnóstico narrativo de la causa de la anomalía.
        recommended_action: Acción sugerida u operativa para resolver o mitigar la anomalía.
        source: Origen real de este texto — "ai" si vino de una llamada
            exitosa a Claude vía tool-use, "template" si es el fallback
            determinista (ya sea porque no hay API key configurada, o
            porque la llamada a Claude falló/agotó iteraciones y se
            delegó silenciosamente). Default "template": es el valor
            correcto para TemplateExplainerAdapter sin que tenga que
            fijarlo explícitamente, y para cualquier implementación
              futura de AIExplainerPort que no lo declare a propósito
            (fail-safe: nunca afirma "ai" por omisión).
    """

    reason: str
    recommended_action: str
    source: Literal["ai", "template"] = "template"


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
