from app.domain.ports.assistant_port import AssistantPort, AssistantResponseDTO


class AskAssistantUseCase:
    """Orquesta la llamada a AssistantPort, sin lógica de negocio propia —
    capa delgada que solo adapta entrada/salida, mismo criterio que
    RegenerateExplanationUseCase."""

    def __init__(self, assistant: AssistantPort) -> None:
        self.assistant = assistant

    def execute(self, conversation: list[dict], pending_confirmation: dict | None) -> AssistantResponseDTO:
        return self.assistant.ask(conversation, pending_confirmation)
