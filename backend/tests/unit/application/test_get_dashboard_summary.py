from datetime import datetime, timezone
from unittest.mock import Mock

from app.application.get_dashboard_summary import GetDashboardSummaryUseCase
from app.domain.models.anomaly import (
    AnomalyRecord,
    AnomalyType,
    Severity,
    AnomalyEvidence,
    PersistedAnomaly,
)
from app.domain.models.anomaly_run import AnalysisRun, AnalysisRunStatus


def _make_persisted_anomaly(severity: Severity, confidence: float, detected_at: datetime) -> PersistedAnomaly:
    evidence = AnomalyEvidence(
        baseline_kwh=10.0,
        observed_kwh=20.0,
        variation_pct=100.0,
        affected_variables=["consumption_kwh"],
        correlated_event=None,
        window_start=detected_at,
        window_end=detected_at,
    )
    record = AnomalyRecord(
        meter_id="M-101",
        detected_at=detected_at,
        type=AnomalyType.REAL_ANOMALY,
        severity=severity,
        confidence=confidence,
        evidence=evidence,
    )
    return PersistedAnomaly(id="a-1", record=record, reason="r", recommended_action="a")


def test_no_anomalies_and_no_run_ever() -> None:
    """CB: base de datos completamente vacía — nunca se corrió un análisis."""
    anomaly_repo = Mock()
    anomaly_repo.get_all.return_value = []
    run_repo = Mock()
    run_repo.get_latest.return_value = None

    uc = GetDashboardSummaryUseCase(meter_repo=Mock(), anomaly_repo=anomaly_repo, run_repo=run_repo)
    dto = uc.execute()

    assert dto.anomalies_detected == 0
    assert dto.high_priority_count == 0
    assert dto.average_confidence is None
    assert dto.last_analysis_at is None


def test_last_analysis_at_reflects_latest_run_even_without_new_anomalies() -> None:
    """Regresión del bug real: antes, last_analysis_at se derivaba de
    max(detected_at) entre anomalías, así que una corrida que no detecta
    nada nuevo no se reflejaba en el dashboard. Ahora debe venir de
    run_repo.get_latest().finished_at, independientemente de si hay
    anomalías."""
    anomaly_repo = Mock()
    anomaly_repo.get_all.return_value = []

    latest_run = AnalysisRun(
        id="run-1",
        requested_meter_id=None,
        status=AnalysisRunStatus.COMPLETED,
        started_at=datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 9, 25, 12, 5, tzinfo=timezone.utc),
        anomalies_detected_count=0,
    )
    run_repo = Mock()
    run_repo.get_latest.return_value = latest_run

    uc = GetDashboardSummaryUseCase(meter_repo=Mock(), anomaly_repo=anomaly_repo, run_repo=run_repo)
    dto = uc.execute()

    assert dto.anomalies_detected == 0
    assert dto.last_analysis_at == datetime(2026, 9, 25, 12, 5, tzinfo=timezone.utc)


def test_aggregates_with_existing_anomalies() -> None:
    anomaly_repo = Mock()
    anomaly_repo.get_all.return_value = [
        _make_persisted_anomaly(Severity.HIGH, 0.9, datetime(2026, 9, 1, tzinfo=timezone.utc)),
        _make_persisted_anomaly(Severity.MEDIUM, 0.7, datetime(2026, 9, 2, tzinfo=timezone.utc)),
        _make_persisted_anomaly(Severity.LOW, 0.5, datetime(2026, 9, 3, tzinfo=timezone.utc)),
    ]

    latest_run = AnalysisRun(
        id="run-2",
        requested_meter_id=None,
        status=AnalysisRunStatus.COMPLETED,
        started_at=datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 9, 25, 10, 1, tzinfo=timezone.utc),
        anomalies_detected_count=3,
    )
    run_repo = Mock()
    run_repo.get_latest.return_value = latest_run

    uc = GetDashboardSummaryUseCase(meter_repo=Mock(), anomaly_repo=anomaly_repo, run_repo=run_repo)
    dto = uc.execute()

    assert dto.anomalies_detected == 3
    assert dto.high_priority_count == 1
    assert dto.average_confidence == (0.9 + 0.7 + 0.5) / 3
    # last_analysis_at viene de la corrida, no de max(detected_at) de las anomalías
    assert dto.last_analysis_at == datetime(2026, 9, 25, 10, 1, tzinfo=timezone.utc)
