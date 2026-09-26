"""Puerto y contratos para el asistente conversacional (SPEC-013)."""

from typing import Protocol
from pydantic import BaseModel


class PendingActionDTO(BaseModel):
    """Acción con side-effect que el modelo propuso pero que aún no se
    ejecutó — requiere confirmación explícita del usuario en la UI.

    Attributes:
        tool: Nombre de la tool propuesta ("run_analysis" o
            "set_triage_status").
        description: Texto en español, ya listo para mostrar en el
            diálogo de confirmación (ej. "¿Confirmas ejecutar el
            análisis para todos los medidores?").
    """

    tool: str
    description: str


class AssistantResponseDTO(BaseModel):
    """Respuesta del asistente a un turno de conversación.

    Attributes:
        text: Texto de respuesta en lenguaje natural. Vacío cuando
            `pending_action` no es None (el turno terminó proponiendo
            una acción, no respondiendo con texto).
        pending_action: Presente si el modelo propuso ejecutar una tool
            con side-effect. El frontend debe mostrar un diálogo de
            confirmación antes de reenviar `pending_confirmation`.
        assistant_message: Mensaje "assistant" crudo del SDK de
            Anthropic (con el bloque tool_use original), presente solo
            cuando `pending_action` no es None. El frontend lo guarda
            en su historial en memoria sin transformarlo y lo reenvía
            intacto dentro de `conversation` al confirmar/cancelar — el
            backend nunca lo reconstruye ni lo cachea entre requests
            (100% stateless).
    """

    text: str
    pending_action: PendingActionDTO | None = None
    assistant_message: dict | None = None


class AssistantPort(Protocol):
    """Puerto que define la interfaz del asistente conversacional."""

    def ask(
        self,
        conversation: list[dict],
        pending_confirmation: dict | None,
    ) -> AssistantResponseDTO:
        """Continúa una conversación con el asistente.

        Args:
            conversation: Mensajes crudos tal como los entrega/consume
                el SDK de `anthropic` (`{"role": ..., "content": str |
                list[dict]}`). El backend es 100% stateless — no
                persiste ni reconstruye este historial entre requests.
            pending_confirmation: `{"confirmed": bool}` si este turno
                responde a un diálogo de confirmación de una acción
                propuesta en el turno anterior, o `None` si es un turno
                normal (pregunta nueva o continuación de tools de
                lectura).

        Returns:
            AssistantResponseDTO con el texto de respuesta, o una
            acción pendiente de confirmación.
        """
        ...
