import pytest
from app.adapters.outbound.persistence.db import create_all_tables, create_db_engine, get_session

@pytest.fixture
def session(tmp_path):
    db_file = tmp_path / "test_anomalies.db"
    engine = create_db_engine(f"sqlite:///{db_file}")
    create_all_tables(engine)
    with get_session(engine) as session:
        yield session

import pytest
from datetime import datetime
from app.adapters.outbound.persistence.anomaly_repository import SqlAlchemyAnomalyRepository
from app.domain.models.anomaly import AnomalyRecord, AnomalyType, Severity, AnomalyEvidence, PersistedAnomaly
from app.domain.ports.ai_explainer_port import AIExplanation

def test_anomaly_repository_save_and_get(session):
    repo = SqlAlchemyAnomalyRepository(session)
    
    ev = AnomalyEvidence(
        baseline_kwh=10.0,
        observed_kwh=20.0,
        variation_pct=100.0,
        affected_variables=["consumption_kwh"],
        correlated_event=None,
        window_start=datetime(2026, 1, 1),
        window_end=datetime(2026, 1, 2),
    )
    
    ar = AnomalyRecord(
        meter_id="M-100",
        detected_at=datetime.utcnow(),
        type=AnomalyType.REAL_ANOMALY,
        severity=Severity.HIGH,
        confidence=0.95,
        evidence=ev
    )
    
    exp = AIExplanation(reason="R", recommended_action="A")
    
    inserted_ids = repo.save_many([(ar, exp)])
    assert len(inserted_ids) == 1
    
    fetched = repo.get_by_id(inserted_ids[0])
    assert fetched is not None
    assert fetched.id == inserted_ids[0]
    assert fetched.reason == "R"
    assert fetched.recommended_action == "A"
    assert fetched.record.meter_id == "M-100"
    assert fetched.record.evidence.variation_pct == 100.0
    assert fetched.record.evidence.affected_variables == ["consumption_kwh"]

def test_anomaly_repository_cb07_double_run(session):
    repo = SqlAlchemyAnomalyRepository(session)
    
    ev = AnomalyEvidence(
        baseline_kwh=10.0,
        observed_kwh=20.0,
        variation_pct=100.0,
        affected_variables=["consumption_kwh"],
        correlated_event=None,
        window_start=datetime(2026, 1, 1),
        window_end=datetime(2026, 1, 2),
    )
    
    ar1 = AnomalyRecord(
        meter_id="M-100",
        detected_at=datetime(2026, 1, 3),
        type=AnomalyType.REAL_ANOMALY,
        severity=Severity.HIGH,
        confidence=0.95,
        evidence=ev
    )
    
    ar2 = AnomalyRecord(
        meter_id="M-100",
        detected_at=datetime(2026, 1, 4),
        type=AnomalyType.REAL_ANOMALY,
        severity=Severity.HIGH,
        confidence=0.95,
        evidence=ev
    )
    
    exp = AIExplanation(reason="R", recommended_action="A")
    
    repo.save_many([(ar1, exp)])
    repo.save_many([(ar2, exp)])
    
    all_anoms = repo.get_by_meter_id("M-100")
    assert len(all_anoms) == 2
    assert all_anoms[0].record.detected_at == datetime(2026, 1, 4) # ordered by desc

