import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from app.domain.models.meter import Meter
from app.domain.models.anomaly_run import AnalysisRunStatus
from app.domain.models.anomaly import AnomalyRecord, AnomalyType, Severity, AnomalyEvidence
from app.domain.ports.ai_explainer_port import AIExplanation
from app.application.analyze_meter import AnalyzeMeterUseCase

def test_analyze_meter_not_found():
    meter_repo = Mock()
    meter_repo.get_by_meter_id.return_value = None
    
    run_repo = Mock()
    
    uc = AnalyzeMeterUseCase(
        meter_repo=meter_repo,
        reading_repo=Mock(),
        event_repo=Mock(),
        anomaly_repo=Mock(),
        run_repo=run_repo,
        explainer=Mock(),
        detector=Mock(),
    )
    
    run = uc.execute("M-999")
    
    assert run.status == AnalysisRunStatus.FAILED
    assert "not found" in run.error_message
    assert run.anomalies_detected_count == 0
    run_repo.save.assert_called_once_with(run)

def test_analyze_all_meters_success():
    meter_repo = Mock()
    meter_repo.get_all.return_value = [Meter(id="1", meter_id="M-1", name="M1", location="L", status="active")]
    
    reading_repo = Mock()
    reading_repo.get_by_meter_id.return_value = []
    
    event_repo = Mock()
    event_repo.get_by_meter_id.return_value = []
    
    anomaly_repo = Mock()
    anomaly_repo.exists.return_value = False  # primera detección, aún no persistida
    anomaly_repo.save_many.return_value = ["new-anomaly-id"]
    run_repo = Mock()
    explainer = Mock()

    detector = Mock()
    ev = AnomalyEvidence(
        baseline_kwh=10, observed_kwh=20, variation_pct=100.0,
        affected_variables=[], correlated_event=None,
        window_start=datetime.utcnow(), window_end=datetime.utcnow()
    )
    anomaly = AnomalyRecord(
        meter_id="M-1", detected_at=datetime.utcnow(),
        type=AnomalyType.REAL_ANOMALY, severity=Severity.HIGH,
        confidence=0.9, evidence=ev
    )
    detector.analyze.return_value = [anomaly]

    exp = AIExplanation(reason="r", recommended_action="a")
    explainer.explain.return_value = exp

    uc = AnalyzeMeterUseCase(
        meter_repo=meter_repo,
        reading_repo=reading_repo,
        event_repo=event_repo,
        anomaly_repo=anomaly_repo,
        run_repo=run_repo,
        explainer=explainer,
        detector=detector,
    )

    run = uc.execute()

    assert run.status == AnalysisRunStatus.COMPLETED
    assert run.anomalies_detected_count == 1
    explainer.explain.assert_called_once_with(anomaly)
    run_repo.save.assert_called_once_with(run)


def test_analyze_all_meters_skips_explainer_for_already_persisted_anomaly():
    """Regresión del bug real de idempotencia: si el detector vuelve a
    encontrar una anomalía cuya ventana (meter_id, type, window_start,
    window_end) ya está persistida, el caso de uso NO debe llamar al
    AIExplainerPort para ella (evita gastar una llamada real y costosa a
    Claude en algo que save_many de todos modos iba a descartar)."""
    meter_repo = Mock()
    meter_repo.get_all.return_value = [Meter(id="1", meter_id="M-1", name="M1", location="L", status="active")]

    reading_repo = Mock()
    reading_repo.get_by_meter_id.return_value = []
    event_repo = Mock()
    event_repo.get_by_meter_id.return_value = []

    anomaly_repo = Mock()
    anomaly_repo.exists.return_value = True  # ya persistida en una corrida anterior
    run_repo = Mock()
    explainer = Mock()

    detector = Mock()
    ev = AnomalyEvidence(
        baseline_kwh=10, observed_kwh=20, variation_pct=100.0,
        affected_variables=[], correlated_event=None,
        window_start=datetime.utcnow(), window_end=datetime.utcnow()
    )
    anomaly = AnomalyRecord(
        meter_id="M-1", detected_at=datetime.utcnow(),
        type=AnomalyType.REAL_ANOMALY, severity=Severity.HIGH,
        confidence=0.9, evidence=ev
    )
    detector.analyze.return_value = [anomaly]

    uc = AnalyzeMeterUseCase(
        meter_repo=meter_repo,
        reading_repo=reading_repo,
        event_repo=event_repo,
        anomaly_repo=anomaly_repo,
        run_repo=run_repo,
        explainer=explainer,
        detector=detector,
    )

    run = uc.execute()

    assert run.status == AnalysisRunStatus.COMPLETED
    assert run.anomalies_detected_count == 0
    explainer.explain.assert_not_called()
    anomaly_repo.save_many.assert_not_called()

def test_analyze_all_meters_tolerates_failure():
    meter_repo = Mock()
    m1 = Meter(id="1", meter_id="M-1", name="M1", location="L", status="active")
    m2 = Meter(id="2", meter_id="M-2", name="M2", location="L", status="active")
    meter_repo.get_all.return_value = [m1, m2]
    
    reading_repo = Mock()
    reading_repo.get_by_meter_id.side_effect = [Exception("Error reading"), []]
    
    detector = Mock()
    detector.analyze.return_value = []
    
    run_repo = Mock()
    
    uc = AnalyzeMeterUseCase(
        meter_repo=meter_repo,
        reading_repo=reading_repo,
        event_repo=Mock(),
        anomaly_repo=Mock(),
        run_repo=run_repo,
        explainer=Mock(),
        detector=detector,
    )
    
    run = uc.execute()
    
    assert run.status == AnalysisRunStatus.COMPLETED
    assert run.error_message is None
