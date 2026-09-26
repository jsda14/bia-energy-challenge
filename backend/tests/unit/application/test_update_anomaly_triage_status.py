from datetime import datetime, timezone
from unittest.mock import Mock

from app.application.update_anomaly_triage_status import UpdateAnomalyTriageStatusUseCase
from app.domain.models.anomaly import (
    AnomalyRecord,
    AnomalyType,
    Severity,
    AnomalyEvidence,
    PersistedAnomaly,
)


def _make_persisted_anomaly(triage_status: str = "NEW") -> PersistedAnomaly:
    evidence = AnomalyEvidence(
        baseline_kwh=19.89,
        observed_kwh=28.02,
        variation_pct=40.9,
        affected_variables=["consumption_kwh"],
        correlated_event=None,
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
    return PersistedAnomaly(
        id="anomaly-1",
        record=record,
        reason="reason",
        recommended_action="action",
        triage_status=triage_status,
    )


def test_returns_none_for_unknown_anomaly() -> None:
    anomaly_repo = Mock()
    anomaly_repo.get_by_id.return_value = None

    uc = UpdateAnomalyTriageStatusUseCase(anomaly_repo=anomaly_repo)
    result = uc.execute("does-not-exist", "ACKNOWLEDGED")

    assert result is None
    anomaly_repo.update_triage_status.assert_not_called()


def test_updates_status_and_returns_dto_reflecting_it() -> None:
    persisted = _make_persisted_anomaly(triage_status="NEW")
    anomaly_repo = Mock()
    anomaly_repo.get_by_id.return_value = persisted

    uc = UpdateAnomalyTriageStatusUseCase(anomaly_repo=anomaly_repo)
    dto = uc.execute("anomaly-1", "ACKNOWLEDGED")

    assert dto is not None
    anomaly_repo.update_triage_status.assert_called_once_with("anomaly-1", "ACKNOWLEDGED")
    assert dto.triage_status == "ACKNOWLEDGED"
    # El resto del detalle permanece intacto — solo cambia triage_status.
    assert dto.reason == "reason"
    assert dto.recommended_action == "action"
    assert dto.type == "DATA_QUALITY"
    assert dto.severity == "HIGH"
    assert dto.meter_id == "M-112"


def test_is_reversible_without_transition_restriction() -> None:
    """Confirma RN de SPEC-013: no hay máquina de estados restringida —
    se puede ir de DISMISSED de vuelta a NEW sin que el use case lo impida."""
    persisted = _make_persisted_anomaly(triage_status="DISMISSED")
    anomaly_repo = Mock()
    anomaly_repo.get_by_id.return_value = persisted

    uc = UpdateAnomalyTriageStatusUseCase(anomaly_repo=anomaly_repo)
    dto = uc.execute("anomaly-1", "NEW")

    assert dto is not None
    assert dto.triage_status == "NEW"
    anomaly_repo.update_triage_status.assert_called_once_with("anomaly-1", "NEW")
