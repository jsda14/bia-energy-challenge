import json
import logging
import anthropic

from app.domain.ports.assistant_port import AssistantPort, AssistantResponseDTO, PendingActionDTO
from app.application.list_anomalies import ListAnomaliesUseCase
from app.application.get_meter_detail import GetMeterDetailUseCase
from app.application.get_dashboard_summary import GetDashboardSummaryUseCase
from app.application.analyze_meter import AnalyzeMeterUseCase
from app.application.update_anomaly_triage_status import UpdateAnomalyTriageStatusUseCase
from app.adapters.outbound.ai.assistant_tools import (
    ALL_TOOL_SCHEMAS,
    execute_get_anomalies_tool,
    execute_get_meter_detail_tool,
    execute_get_dashboard_summary_tool,
)

logger = logging.getLogger(__name__)

GENERIC_ERROR_MESSAGE = "Hubo un error al contactar al asistente. Intenta de nuevo más tarde."


class ClaudeAssistantAdapter(AssistantPort):
    """Asistente conversacional que usa el SDK de Anthropic (Claude)
    mediante un bucle de agentes (tool calling), mismo patrón que
    `ClaudeExplainerAdapter` (SPEC-004). Sin fallback a plantilla — a
    diferencia de la explicación de anomalías, un asistente conversacional
    no tiene un fallback determinista sensato; cualquier fallo cae al
    mensaje de error genérico en español.

    Punto central de seguridad: `run_analysis`/`set_triage_status`
    (SIDE_EFFECT_TOOLS) NUNCA se ejecutan dentro del loop principal — solo
    generan un `pending_action` y cortan el turno inmediatamente. La única
    vía de ejecución real es `_execute_side_effect_tool`, llamada
    exclusivamente cuando `pending_confirmation == {"confirmed": True}`
    llega en un request posterior, explícito, disparado por un click del
    usuario en la UI.
    """

    MAX_ITERATIONS = 5
    SIDE_EFFECT_TOOLS = {"run_analysis", "set_triage_status"}

    def __init__(
        self,
        list_anomalies_uc: ListAnomaliesUseCase,
        get_meter_detail_uc: GetMeterDetailUseCase,
        get_dashboard_summary_uc: GetDashboardSummaryUseCase,
        analyze_meter_uc: AnalyzeMeterUseCase,
        update_triage_status_uc: UpdateAnomalyTriageStatusUseCase,
        api_key: str,
        model: str,
    ) -> None:
        self._list_anomalies_uc = list_anomalies_uc
        self._get_meter_detail_uc = get_meter_detail_uc
        self._get_dashboard_summary_uc = get_dashboard_summary_uc
        self._analyze_meter_uc = analyze_meter_uc
        self._update_triage_status_uc = update_triage_status_uc
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def ask(self, conversation: list[dict], pending_confirmation: dict | None) -> AssistantResponseDTO:
        try:
            messages = list(conversation)

            if pending_confirmation is not None:
                messages.append(self._resolve_pending_confirmation(messages, pending_confirmation))

            for _ in range(self.MAX_ITERATIONS):
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=1000,
                    messages=messages,
                    tools=ALL_TOOL_SCHEMAS,
                    system=(
                        "You are Bia Energy's assistant for meter/anomaly triage. "
                        "Respond in Spanish (es-ES) — the entire system is in "
                        "Spanish. When proposing run_analysis or "
                        "set_triage_status, call the tool — the system will "
                        "handle asking the user for confirmation; you never "
                        "need to ask for it yourself in text."
                    ),
                )

                if response.stop_reason != "tool_use":
                    text = next((b.text for b in response.content if b.type == "text"), "")
                    return AssistantResponseDTO(text=text)

                side_effect_block = next(
                    (b for b in response.content if b.type == "tool_use" and b.name in self.SIDE_EFFECT_TOOLS),
                    None,
                )
                if side_effect_block is not None:
                    # PUNTO CENTRAL DE SEGURIDAD: se corta el loop aquí,
                    # nunca se llama a un use case con side-effect en esta
                    # rama. Se retorna la propuesta + el mensaje assistant
                    # crudo, para que el frontend lo reenvíe intacto si el
                    # usuario confirma.
                    return AssistantResponseDTO(
                        text="",
                        pending_action=PendingActionDTO(
                            tool=side_effect_block.name,
                            description=self._describe_action(side_effect_block),
                        ),
                        assistant_message={"role": "assistant", "content": response.content},
                    )

                messages.append({"role": "assistant", "content": response.content})
                tool_results = [
                    self._execute_read_tool(block) for block in response.content if block.type == "tool_use"
                ]
                messages.append({"role": "user", "content": tool_results})

            return AssistantResponseDTO(text="No pude completar la consulta, intenta reformularla.")
        except Exception as e:
            logger.warning(f"Assistant call failed: {e}")
            return AssistantResponseDTO(text=GENERIC_ERROR_MESSAGE)

    def _resolve_pending_confirmation(self, messages: list[dict], pending_confirmation: dict) -> dict:
        """Arma el turno "user" con el tool_result que resuelve la acción
        pendiente — ejecutándola de verdad si el usuario confirmó, o
        marcándola como cancelada si no. El tool_use pendiente se lee del
        último mensaje "assistant" en `conversation` (que el frontend ya
        reenvía intacto, ver AssistantPort.ask)."""
        last_assistant = messages[-1]
        tool_use_block = next(
            b for b in last_assistant["content"] if isinstance(b, dict) and b.get("type") == "tool_use"
        )

        if pending_confirmation.get("confirmed"):
            result_content = self._execute_side_effect_tool(tool_use_block["name"], tool_use_block["input"])
            tool_result = {
                "type": "tool_result",
                "tool_use_id": tool_use_block["id"],
                "content": json.dumps(result_content),
            }
        else:
            tool_result = {
                "type": "tool_result",
                "tool_use_id": tool_use_block["id"],
                "content": "El usuario canceló la acción.",
                "is_error": True,
            }
        return {"role": "user", "content": [tool_result]}

    def _execute_side_effect_tool(self, name: str, tool_input: dict) -> dict:
        """ÚNICO lugar del adapter que invoca un use case con side-effect.
        Solo se llama desde `_resolve_pending_confirmation`, cuando
        `pending_confirmation.confirmed is True` — nunca desde el loop
        principal de `ask`."""
        if name == "run_analysis":
            run = self._analyze_meter_uc.execute(tool_input.get("meter_id"))
            return {
                "status": run.status.value,
                "anomalies_detected_count": run.anomalies_detected_count,
                "error_message": run.error_message,
            }
        if name == "set_triage_status":
            dto = self._update_triage_status_uc.execute(tool_input["anomaly_id"], tool_input["status"])
            if dto is None:
                return {"error": f"Anomaly '{tool_input['anomaly_id']}' not found"}
            return {"id": dto.id, "triage_status": dto.triage_status}
        return {"error": f"Unknown side-effect tool: {name}"}

    def _execute_read_tool(self, block) -> dict:
        try:
            if block.name == "get_anomalies":
                result = execute_get_anomalies_tool(
                    self._list_anomalies_uc, block.input.get("severity"), block.input.get("meter_id")
                )
            elif block.name == "get_meter_detail":
                result = execute_get_meter_detail_tool(self._get_meter_detail_uc, block.input["meter_id"])
            elif block.name == "get_dashboard_summary":
                result = execute_get_dashboard_summary_tool(self._get_dashboard_summary_uc)
            else:
                return {"type": "tool_result", "tool_use_id": block.id, "content": "Error: Unknown tool", "is_error": True}
            return {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)}
        except Exception as e:
            return {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": f"Error executing tool: {e}",
                "is_error": True,
            }

    def _describe_action(self, block) -> str:
        if block.name == "run_analysis":
            meter_id = block.input.get("meter_id")
            if meter_id:
                return f"¿Confirmas ejecutar el análisis para el medidor {meter_id}?"
            return "¿Confirmas ejecutar el análisis para todos los medidores?"
        if block.name == "set_triage_status":
            anomaly_id = block.input.get("anomaly_id")
            status = block.input.get("status")
            status_label = {"NEW": "Nueva", "ACKNOWLEDGED": "Atendida", "DISMISSED": "Descartada"}.get(status, status)
            return f"¿Confirmas marcar la anomalía {anomaly_id} como {status_label}?"
        return f"¿Confirmas ejecutar la acción '{block.name}'?"
