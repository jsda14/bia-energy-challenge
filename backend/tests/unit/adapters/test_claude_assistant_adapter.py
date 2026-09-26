import pytest
from unittest.mock import Mock, patch, MagicMock

from app.adapters.outbound.ai.claude_assistant_adapter import ClaudeAssistantAdapter, GENERIC_ERROR_MESSAGE


@pytest.fixture
def use_cases():
    return {
        "list_anomalies_uc": Mock(),
        "get_meter_detail_uc": Mock(),
        "get_dashboard_summary_uc": Mock(),
        "analyze_meter_uc": Mock(),
        "update_triage_status_uc": Mock(),
    }


def _make_adapter(use_cases):
    return ClaudeAssistantAdapter(
        list_anomalies_uc=use_cases["list_anomalies_uc"],
        get_meter_detail_uc=use_cases["get_meter_detail_uc"],
        get_dashboard_summary_uc=use_cases["get_dashboard_summary_uc"],
        analyze_meter_uc=use_cases["analyze_meter_uc"],
        update_triage_status_uc=use_cases["update_triage_status_uc"],
        api_key="fake-key",
        model="fake-model",
    )


def test_ask_returns_plain_text_when_no_tool_use(use_cases):
    with patch("app.adapters.outbound.ai.claude_assistant_adapter.anthropic.Anthropic") as mock_anthropic:
        mock_client = mock_anthropic.return_value
        msg = MagicMock()
        msg.stop_reason = "end_turn"
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Hola, ¿en qué puedo ayudarte?"
        msg.content = [text_block]
        mock_client.messages.create.return_value = msg

        adapter = _make_adapter(use_cases)
        result = adapter.ask([{"role": "user", "content": "hola"}], None)

        assert result.text == "Hola, ¿en qué puedo ayudarte?"
        assert result.pending_action is None
        assert result.assistant_message is None


def test_ask_executes_read_tool_and_continues_loop(use_cases):
    use_cases["list_anomalies_uc"].execute.return_value = []

    with patch("app.adapters.outbound.ai.claude_assistant_adapter.anthropic.Anthropic") as mock_anthropic:
        mock_client = mock_anthropic.return_value

        msg1 = MagicMock()
        msg1.stop_reason = "tool_use"
        block1 = MagicMock()
        block1.type = "tool_use"
        block1.name = "get_anomalies"
        block1.id = "tool_1"
        block1.input = {"severity": None, "meter_id": None}
        msg1.content = [block1]

        msg2 = MagicMock()
        msg2.stop_reason = "end_turn"
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "No hay anomalías."
        msg2.content = [text_block]

        mock_client.messages.create.side_effect = [msg1, msg2]

        adapter = _make_adapter(use_cases)
        result = adapter.ask([{"role": "user", "content": "¿hay anomalías?"}], None)

        assert result.text == "No hay anomalías."
        use_cases["list_anomalies_uc"].execute.assert_called_once_with(None)
        # Ningún use case con side-effect fue tocado en este flujo de solo lectura.
        use_cases["analyze_meter_uc"].execute.assert_not_called()
        use_cases["update_triage_status_uc"].execute.assert_not_called()


def test_ask_returns_pending_action_for_run_analysis_without_executing_it(use_cases):
    """PUNTO CENTRAL DE SEGURIDAD: cuando el modelo propone run_analysis,
    el adapter debe cortar el loop y devolver pending_action sin haber
    llamado a AnalyzeMeterUseCase."""
    with patch("app.adapters.outbound.ai.claude_assistant_adapter.anthropic.Anthropic") as mock_anthropic:
        mock_client = mock_anthropic.return_value
        msg = MagicMock()
        msg.stop_reason = "tool_use"
        block = MagicMock()
        block.type = "tool_use"
        block.name = "run_analysis"
        block.id = "tool_1"
        block.input = {"meter_id": None}
        msg.content = [block]
        mock_client.messages.create.return_value = msg

        adapter = _make_adapter(use_cases)
        result = adapter.ask([{"role": "user", "content": "corré el análisis"}], None)

        assert result.text == ""
        assert result.pending_action is not None
        assert result.pending_action.tool == "run_analysis"
        assert "todos los medidores" in result.pending_action.description
        assert result.assistant_message == {"role": "assistant", "content": msg.content}
        # LA PARTE QUE IMPORTA: nunca se ejecutó.
        use_cases["analyze_meter_uc"].execute.assert_not_called()
        assert mock_client.messages.create.call_count == 1


def test_ask_returns_pending_action_for_set_triage_status_without_executing_it(use_cases):
    with patch("app.adapters.outbound.ai.claude_assistant_adapter.anthropic.Anthropic") as mock_anthropic:
        mock_client = mock_anthropic.return_value
        msg = MagicMock()
        msg.stop_reason = "tool_use"
        block = MagicMock()
        block.type = "tool_use"
        block.name = "set_triage_status"
        block.id = "tool_1"
        block.input = {"anomaly_id": "anomaly-1", "status": "DISMISSED"}
        msg.content = [block]
        mock_client.messages.create.return_value = msg

        adapter = _make_adapter(use_cases)
        result = adapter.ask([{"role": "user", "content": "descartá esa anomalía"}], None)

        assert result.pending_action.tool == "set_triage_status"
        assert "anomaly-1" in result.pending_action.description
        assert "Descartada" in result.pending_action.description
        use_cases["update_triage_status_uc"].execute.assert_not_called()


def test_ask_confirmed_true_executes_the_pending_side_effect_tool(use_cases):
    """El único camino real de ejecución: pending_confirmation confirmed=True
    en un request posterior, con el assistant_message pendiente reenviado
    tal cual por el frontend."""
    use_cases["analyze_meter_uc"].execute.return_value = Mock(
        status=Mock(value="COMPLETED"), anomalies_detected_count=2, error_message=None
    )

    pending_tool_use_block = {
        "type": "tool_use",
        "id": "tool_1",
        "name": "run_analysis",
        "input": {"meter_id": None},
    }
    conversation = [
        {"role": "user", "content": "corré el análisis"},
        {"role": "assistant", "content": [pending_tool_use_block]},
    ]

    with patch("app.adapters.outbound.ai.claude_assistant_adapter.anthropic.Anthropic") as mock_anthropic:
        mock_client = mock_anthropic.return_value
        closing_msg = MagicMock()
        closing_msg.stop_reason = "end_turn"
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Listo, corrí el análisis para todos los medidores."
        closing_msg.content = [text_block]
        mock_client.messages.create.return_value = closing_msg

        adapter = _make_adapter(use_cases)
        result = adapter.ask(conversation, {"confirmed": True})

        use_cases["analyze_meter_uc"].execute.assert_called_once_with(None)
        assert result.text == "Listo, corrí el análisis para todos los medidores."
        assert result.pending_action is None

        # El tool_result enviado de vuelta a Claude refleja el resultado real.
        call_args = mock_client.messages.create.call_args_list[0][1]
        tool_result_message = call_args["messages"][-1]
        assert tool_result_message["role"] == "user"
        assert tool_result_message["content"][0]["type"] == "tool_result"
        assert tool_result_message["content"][0]["tool_use_id"] == "tool_1"


def test_ask_confirmed_false_never_executes_the_side_effect_tool(use_cases):
    """PUNTO CENTRAL DE SEGURIDAD (complemento): confirmed=False jamás
    ejecuta la acción, sin importar qué tool estuviera pendiente."""
    pending_tool_use_block = {
        "type": "tool_use",
        "id": "tool_1",
        "name": "set_triage_status",
        "input": {"anomaly_id": "anomaly-1", "status": "DISMISSED"},
    }
    conversation = [
        {"role": "user", "content": "descartá esa anomalía"},
        {"role": "assistant", "content": [pending_tool_use_block]},
    ]

    with patch("app.adapters.outbound.ai.claude_assistant_adapter.anthropic.Anthropic") as mock_anthropic:
        mock_client = mock_anthropic.return_value
        closing_msg = MagicMock()
        closing_msg.stop_reason = "end_turn"
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Entendido, no se realizó ningún cambio."
        closing_msg.content = [text_block]
        mock_client.messages.create.return_value = closing_msg

        adapter = _make_adapter(use_cases)
        result = adapter.ask(conversation, {"confirmed": False})

        use_cases["update_triage_status_uc"].execute.assert_not_called()
        assert result.text == "Entendido, no se realizó ningún cambio."

        call_args = mock_client.messages.create.call_args_list[0][1]
        tool_result_message = call_args["messages"][-1]
        assert tool_result_message["content"][0]["is_error"] is True


def test_ask_falls_back_to_generic_error_message_on_exception(use_cases):
    with patch("app.adapters.outbound.ai.claude_assistant_adapter.anthropic.Anthropic") as mock_anthropic:
        mock_client = mock_anthropic.return_value
        mock_client.messages.create.side_effect = Exception("Network timeout")

        adapter = _make_adapter(use_cases)
        result = adapter.ask([{"role": "user", "content": "hola"}], None)

        assert result.text == GENERIC_ERROR_MESSAGE
        assert result.pending_action is None


def test_ask_exhausts_max_iterations_on_read_tool_loop(use_cases):
    use_cases["get_dashboard_summary_uc"].execute.return_value = Mock(
        anomalies_detected=0, high_priority_count=0, average_confidence=None, last_analysis_at=None
    )

    with patch("app.adapters.outbound.ai.claude_assistant_adapter.anthropic.Anthropic") as mock_anthropic:
        mock_client = mock_anthropic.return_value
        msg = MagicMock()
        msg.stop_reason = "tool_use"
        block = MagicMock()
        block.type = "tool_use"
        block.name = "get_dashboard_summary"
        block.id = "tool_1"
        block.input = {}
        msg.content = [block]
        mock_client.messages.create.return_value = msg

        adapter = _make_adapter(use_cases)
        result = adapter.ask([{"role": "user", "content": "resumen"}], None)

        assert result.text == "No pude completar la consulta, intenta reformularla."
        assert mock_client.messages.create.call_count == adapter.MAX_ITERATIONS
