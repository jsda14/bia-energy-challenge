from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.adapters.inbound.api.dependencies import get_ask_assistant_use_case
from app.application.ask_assistant import AskAssistantUseCase

router = APIRouter(prefix="/assistant", tags=["Assistant"])


class PendingConfirmation(BaseModel):
    confirmed: bool


class PendingActionResponse(BaseModel):
    tool: str
    description: str


class AssistantAskRequest(BaseModel):
    # Mensajes crudos del SDK de Anthropic — {"role": ..., "content": str
    # | list[dict]}. No se valida la forma interna de `content` con un
    # schema Pydantic estricto: es un pass-through opaco hacia/desde
    # anthropic.Anthropic, el frontend nunca lo interpreta, solo lo guarda
    # y reenvía tal cual (SPEC-013 sección 1.2).
    conversation: list[dict]
    pending_confirmation: PendingConfirmation | None = None


class AssistantAskResponse(BaseModel):
    text: str
    pending_action: PendingActionResponse | None = None
    assistant_message: dict | None = None


@router.post("/ask", response_model=AssistantAskResponse)
def ask_assistant(
    request: AssistantAskRequest,
    use_case: AskAssistantUseCase = Depends(get_ask_assistant_use_case),
):
    """Continúa una conversación con el asistente. Backend 100% stateless
    — el frontend mantiene y reenvía `conversation` completo en cada
    request (sin sesiones, sin autenticación, consistente con el resto
    del MVP)."""
    result = use_case.execute(
        conversation=request.conversation,
        pending_confirmation=request.pending_confirmation.model_dump() if request.pending_confirmation else None,
    )
    return AssistantAskResponse(
        text=result.text,
        pending_action=PendingActionResponse(**result.pending_action.model_dump()) if result.pending_action else None,
        assistant_message=result.assistant_message,
    )
