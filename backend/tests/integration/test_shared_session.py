import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from app.adapters.outbound.persistence.db import create_all_tables, get_session
from app.adapters.outbound.persistence.anomaly_repository import SqlAlchemyAnomalyRepository
from app.adapters.outbound.persistence.anomaly_run_repository import SqlAlchemyAnomalyRunRepository

from app.domain.models.anomaly_run import AnalysisRun, AnalysisRunStatus
from app.domain.models.anomaly import AnomalyRecord, AnomalyType, Severity, AnomalyEvidence
from app.domain.ports.ai_explainer_port import AIExplanation

def get_test_engine():
    engine = create_engine('sqlite:///:memory:')
    create_all_tables(engine)
    return engine

def test_shared_session_atomicity():
    engine = get_test_engine()
    
    with get_session(engine) as session:
        anomaly_repo = SqlAlchemyAnomalyRepository(session)
        run_repo = SqlAlchemyAnomalyRunRepository(session)
        
        ev = AnomalyEvidence(
            baseline_kwh=10.0,
            observed_kwh=20.0,
            variation_pct=100.0,
            affected_variables=['consumption_kwh'],
            correlated_event=None,
            window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            window_end=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
        
        ar = AnomalyRecord(
            meter_id='M-SHARED',
            detected_at=datetime.now(timezone.utc),
            type=AnomalyType.REAL_ANOMALY,
            severity=Severity.HIGH,
            confidence=0.95,
            evidence=ev
        )
        
        exp = AIExplanation(reason='R', recommended_action='A')
        
        inserted_ids = anomaly_repo.save_many([(ar, exp)])
        
        run_id = str(uuid.uuid4())
        run = AnalysisRun(
            id=run_id,
            requested_meter_id='M-SHARED',
            status=AnalysisRunStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            anomalies_detected_count=1,
            error_message=None
        )
        run_repo.save(run)
        
        fetched_run = run_repo.get_by_id(run_id)
        fetched_anoms = anomaly_repo.get_by_meter_id('M-SHARED')
        
        assert fetched_run is not None
        assert len(fetched_anoms) == 1
        assert fetched_anoms[0].id == inserted_ids[0]

def test_transaction_rollback_atomicity():
    # Este test comprueba explícitamente que un flush no guarda en disco si ocurre rollback.
    engine = get_test_engine()
    
    # 1. Abrimos sesión, hacemos flush vía save_many y simulamos un fallo con rollback.
    session = get_session(engine)
    try:
        anomaly_repo = SqlAlchemyAnomalyRepository(session)
        ev = AnomalyEvidence(
            baseline_kwh=10.0,
            observed_kwh=20.0,
            variation_pct=100.0,
            affected_variables=['consumption_kwh'],
            correlated_event=None,
            window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            window_end=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
        
        ar = AnomalyRecord(
            meter_id='M-ROLLBACK',
            detected_at=datetime.now(timezone.utc),
            type=AnomalyType.REAL_ANOMALY,
            severity=Severity.HIGH,
            confidence=0.95,
            evidence=ev
        )
        exp = AIExplanation(reason='R', recommended_action='A')
        
        # El save_many hace session.flush() internamente, no commit.
        anomaly_repo.save_many([(ar, exp)])
        
        # 2. Simulamos el fallo
        raise RuntimeError('Fallo simulado')
    except RuntimeError:
        session.rollback()
    finally:
        session.close()
        
    # 3. Abrimos una nueva sesión distinta.
    new_session = get_session(engine)
    try:
        new_repo = SqlAlchemyAnomalyRepository(new_session)
        # 4. Assert que no se guardó nada en disco.
        fetched = new_repo.get_by_meter_id('M-ROLLBACK')
        assert len(fetched) == 0
    finally:
        new_session.close()

