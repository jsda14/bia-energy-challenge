from datetime import datetime, timezone
from unittest.mock import Mock

from app.application.regenerate_explanation import RegenerateExplanationUseCase
from app.domain.models.anomaly import (
    AnomalyRecord,
    AnomalyType,
    Severity,
    AnomalyEvidence,
    PersistedAnomaly,
)
from app.domain.ports.ai_explainer_port import AIExplanation


def _make_persisted_anomaly() -> PersistedAnomaly:
    evidence = AnomalyEvidence(
        baseline_kwh=19.89,
        observed_kwh=28.02,
        variation_pct=40.9,
        affected_variables=["consumption_kwh", "current_a", "power_factor"],
        correlated_event="Intermittent readings and abnormal electrical jumps",
        window_start=datetime(2026, 9, 13, 3, 0, tzinfo=timezone.utc),
        window_end=datetime(2026, 9, 14, 21, 0, tzinfo=timezone.utc),
    )
    record = AnomalyRecord(
        meter_id="M-112",
        detected_at=datetime(2026, 9, 13, 3, 0, tzinfo=timezone.utc),
        type=AnomalyType.DATA_QUALITY,
        severity=Severity.HIGH,
        confidence=0.83,
        evidence=evidence,
    )
    return PersistedAnomaly(id="anomaly-1", record=record, reason="old reason", recommended_action="old action")


def test_returns_none_for_unknown_anomaly() -> None:
    anomaly_repo = Mock()
    anomaly_repo.get_by_id.return_value = None
    explainer = Mock()

    uc = RegenerateExplanationUseCase(anomaly_repo=anomaly_repo, explainer=explainer)
    result = uc.execute("does-not-exist")

    assert result is None
    explainer.explain.assert_not_called()
    anomaly_repo.update_explanation.assert_not_called()


def test_calls_explainer_and_persists_new_explanation() -> None:
    persisted = _make_persisted_anomaly()
    anomaly_repo = Mock()
    anomaly_repo.get_by_id.return_value = persisted

    new_explanation = AIExplanation(reason="Nueva razón generada", recommended_action="Nueva acción recomendada")
    explainer = Mock()
    explainer.explain.return_value = new_explanation

    uc = RegenerateExplanationUseCase(anomaly_repo=anomaly_repo, explainer=explainer)
    dto = uc.execute("anomaly-1")

    assert dto is not None
    # El explainer se llama con el AnomalyRecord ya reconstruido, no con la
    # explicación vieja — la detección/evidencia no cambia, solo el texto.
    explainer.explain.assert_called_once_with(persisted.record)
    anomaly_repo.update_explanation.assert_called_once_with("anomaly-1", new_explanation)

    # El DTO devuelto refleja la explicación NUEVA, no la vieja persistida.
    assert dto.reason == "Nueva razón generada"
    assert dto.recommended_action == "Nueva acción recomendada"
    # El resto de los datos de detección permanece intacto (no es una
    # nueva detección, solo una nueva explicación sobre el mismo incidente).
    assert dto.type == "DATA_QUALITY"
    assert dto.severity == "HIGH"
    assert dto.confidence == 0.83
    assert dto.meter_id == "M-112"
