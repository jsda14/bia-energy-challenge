import json
import logging
import anthropic
from app.domain.ports.ai_explainer_port import AIExplainerPort, AIExplanation
from app.domain.ports.event_repository_port import EventRepositoryPort
from app.domain.models.anomaly import AnomalyRecord
from app.adapters.outbound.ai.template_explainer_adapter import TemplateExplainerAdapter
from app.adapters.outbound.ai.claude_tools import (
    GET_EVENTS_TOOL_SCHEMA, 
    SUBMIT_EXPLANATION_TOOL_SCHEMA, 
    execute_get_events_tool
)

logger = logging.getLogger(__name__)

class ClaudeExplainerAdapter(AIExplainerPort):
    """Adaptador de IA que utiliza el SDK de Anthropic (Claude) mediante un bucle de agentes (tool calling)
    para analizar anomalías y requerir de eventos operativos en caso de ser necesario.
    """

    MAX_ITERATIONS = 3

    def __init__(self, event_repo: EventRepositoryPort, api_key: str, model: str) -> None:
        """Inicializa el adaptador con el cliente de Anthropic.

        Args:
            event_repo: El repositorio para inyectar en las consultas de eventos.
            api_key: La clave de la API de Anthropic.
            model: El modelo a invocar de Anthropic (por ejemplo, 'claude-3-5-sonnet-20240620').
        """
        self._event_repo = event_repo
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._fallback = TemplateExplainerAdapter()

    def explain(self, anomaly: AnomalyRecord) -> AIExplanation:
        """Genera una explicación de la anomalía iterando con Claude mediante tool calls.
        Si ocurre cualquier error de red, timeout, rate limit o validación, 
        delega silenciosamente al TemplateExplainerAdapter.

        Args:
            anomaly: El registro de la anomalía a explicar.

        Returns:
            AIExplanation generado por Claude o por el fallback determinista.
        """
        try:
            messages = [{
                "role": "user",
                "content": (
                    f"Analyze this anomaly for meter {anomaly.meter_id}: {anomaly.evidence}\n\n"
                    "Respond in Spanish (es-ES) — the entire system (UI, other "
                    "explanations, recommended actions) is in Spanish, and the "
                    "output must be consistent with it. Do not switch to "
                    "English even though this instruction and the tool "
                    "schemas are in English."
                ),
            }]
            
            for _ in range(self.MAX_ITERATIONS):
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=1000,
                    messages=messages,
                    tools=[GET_EVENTS_TOOL_SCHEMA, SUBMIT_EXPLANATION_TOOL_SCHEMA],
                )
                
                if response.stop_reason == "tool_use":
                    messages.append({"role": "assistant", "content": response.content})
                    tool_results = []
                    
                    for block in response.content:
                        if block.type == "tool_use":
                            if block.name == "get_events":
                                events = execute_get_events_tool(self._event_repo, block.input.get("meter_id"))
                                tool_results.append({
                                    "type": "tool_result", 
                                    "tool_use_id": block.id, 
                                    "content": json.dumps(events)
                                })
                            elif block.name == "submit_explanation":
                                # Pydantic will validate the required fields. If missing, it raises ValidationError
                                # which is caught by the broad except Exception block and triggers fallback.
                                return AIExplanation(**block.input)
                            else:
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": "Error: Unknown tool",
                                    "is_error": True
                                })
                                
                    messages.append({"role": "user", "content": tool_results})
                else:
                    # Model responded with text instead of calling the submit_explanation tool
                    break
                    
            # Fallback if iterations exhausted or tool not used correctly
            return self._fallback.explain(anomaly)
            
        except Exception as e:
            logger.warning(f"Claude API failed: {e}. Falling back to template.")
            return self._fallback.explain(anomaly)
