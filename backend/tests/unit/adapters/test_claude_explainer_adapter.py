import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.domain.models.anomaly import AnomalyRecord, AnomalyType, Severity, AnomalyEvidence
from app.domain.models.event import Event, EventType
from app.domain.ports.ai_explainer_port import AIExplanation
from app.adapters.outbound.ai.claude_explainer_adapter import ClaudeExplainerAdapter
from app.adapters.outbound.ai.template_explainer_adapter import TemplateExplainerAdapter

@pytest.fixture
def mock_event_repo():
    repo = Mock()
    repo.get_by_meter_id.return_value = []
    return repo

@pytest.fixture
def anomaly_record():
    return AnomalyRecord(
        meter_id="M-101",
        detected_at=datetime.utcnow(),
        type=AnomalyType.REAL_ANOMALY,
        severity=Severity.HIGH,
        confidence=0.9,
        evidence=AnomalyEvidence(
            baseline_kwh=10.0,
            observed_kwh=20.0,
            variation_pct=100.0,
            affected_variables=["consumption_kwh"],
            correlated_event=None,
            window_start=datetime.utcnow(),
            window_end=datetime.utcnow()
        )
    )

def test_explain_normal_flow(mock_event_repo, anomaly_record):
    with patch("app.adapters.outbound.ai.claude_explainer_adapter.anthropic.Anthropic") as mock_anthropic:
        mock_client = mock_anthropic.return_value
        
        # Iteration 1: calls get_events tool
        msg1 = MagicMock()
        msg1.stop_reason = "tool_use"
        block1 = MagicMock()
        block1.type = "tool_use"
        block1.name = "get_events"
        block1.id = "tool_1"
        block1.input = {"meter_id": "M-101"}
        msg1.content = [block1]
        
        # Iteration 2: calls submit_explanation tool
        msg2 = MagicMock()
        msg2.stop_reason = "tool_use"
        block2 = MagicMock()
        block2.type = "tool_use"
        block2.name = "submit_explanation"
        block2.id = "tool_2"
        block2.input = {"reason": "The voltage dropped.", "recommended_action": "Check wiring."}
        msg2.content = [block2]
        
        mock_client.messages.create.side_effect = [msg1, msg2]
        
        adapter = ClaudeExplainerAdapter(mock_event_repo, "fake-key", "fake-model")
        explanation = adapter.explain(anomaly_record)
        
        assert explanation.reason == "The voltage dropped."
        assert explanation.recommended_action == "Check wiring."
        assert mock_client.messages.create.call_count == 2
        mock_event_repo.get_by_meter_id.assert_called_once_with("M-101")

def test_explain_fallback_on_exception(mock_event_repo, anomaly_record):
    with patch("app.adapters.outbound.ai.claude_explainer_adapter.anthropic.Anthropic") as mock_anthropic:
        mock_client = mock_anthropic.return_value
        mock_client.messages.create.side_effect = Exception("Network timeout")
        
        adapter = ClaudeExplainerAdapter(mock_event_repo, "fake-key", "fake-model")
        explanation = adapter.explain(anomaly_record)
        
        # Debe usar el TemplateExplainerAdapter silenciosamente
        fallback = TemplateExplainerAdapter()
        expected = fallback.explain(anomaly_record)
        
        assert explanation.reason == expected.reason
        assert explanation.recommended_action == expected.recommended_action
        assert mock_client.messages.create.call_count == 1

def test_explain_fallback_missing_tool_args(mock_event_repo, anomaly_record):
    with patch("app.adapters.outbound.ai.claude_explainer_adapter.anthropic.Anthropic") as mock_anthropic:
        mock_client = mock_anthropic.return_value
        
        # Claude uses submit_explanation but omits fields
        msg = MagicMock()
        msg.stop_reason = "tool_use"
        block = MagicMock()
        block.type = "tool_use"
        block.name = "submit_explanation"
        block.id = "tool_1"
        block.input = {"reason": "Missing action"} # Missing recommended_action
        msg.content = [block]
        
        mock_client.messages.create.side_effect = [msg]
        
        adapter = ClaudeExplainerAdapter(mock_event_repo, "fake-key", "fake-model")
        explanation = adapter.explain(anomaly_record)
        
        # Validates that Pydantic validation error is caught and fallback triggered
        fallback = TemplateExplainerAdapter()
        expected = fallback.explain(anomaly_record)
        assert explanation.reason == expected.reason

def test_explain_max_iterations_exhausted(mock_event_repo, anomaly_record):
    with patch("app.adapters.outbound.ai.claude_explainer_adapter.anthropic.Anthropic") as mock_anthropic:
        mock_client = mock_anthropic.return_value
        
        msg = MagicMock()
        msg.stop_reason = "tool_use"
        block = MagicMock()
        block.type = "tool_use"
        block.name = "get_events"
        block.id = "tool_1"
        block.input = {"meter_id": "M-101"}
        msg.content = [block]
        
        # Siempre llama a get_events
        mock_client.messages.create.return_value = msg
        
        adapter = ClaudeExplainerAdapter(mock_event_repo, "fake-key", "fake-model")
        explanation = adapter.explain(anomaly_record)
        
        fallback = TemplateExplainerAdapter()
        expected = fallback.explain(anomaly_record)
        assert explanation.reason == expected.reason
        assert mock_client.messages.create.call_count == adapter.MAX_ITERATIONS

def test_explain_handles_multiple_tools_and_unknown(mock_event_repo, anomaly_record):
    with patch("app.adapters.outbound.ai.claude_explainer_adapter.anthropic.Anthropic") as mock_anthropic:
        mock_client = mock_anthropic.return_value
        
        msg1 = MagicMock()
        msg1.stop_reason = "tool_use"
        
        block1 = MagicMock()
        block1.type = "tool_use"
        block1.name = "get_events"
        block1.id = "tool_1"
        block1.input = {"meter_id": "M-101"}
        
        block_unknown = MagicMock()
        block_unknown.type = "tool_use"
        block_unknown.name = "unknown_tool"
        block_unknown.id = "tool_unknown"
        block_unknown.input = {}
        
        msg1.content = [block1, block_unknown]
        
        msg2 = MagicMock()
        msg2.stop_reason = "tool_use"
        block2 = MagicMock()
        block2.type = "tool_use"
        block2.name = "submit_explanation"
        block2.id = "tool_2"
        block2.input = {"reason": "Test", "recommended_action": "Test"}
        msg2.content = [block2]
        
        mock_client.messages.create.side_effect = [msg1, msg2]
        
        adapter = ClaudeExplainerAdapter(mock_event_repo, "fake-key", "fake-model")
        explanation = adapter.explain(anomaly_record)
        
        assert explanation.reason == "Test"
        assert mock_client.messages.create.call_count == 2
        
        # Verify that tool_results properly collected two elements in iteration 1
        # Due to mutability, the messages list at the end of the test has 4 elements:
        # [0] user, [1] assistant (msg1), [2] user (tool results), [3] assistant (msg2)
        call_args = mock_client.messages.create.call_args_list[1][1]
        tool_results_message = call_args["messages"][2]
        assert tool_results_message["role"] == "user"
        assert len(tool_results_message["content"]) == 2
