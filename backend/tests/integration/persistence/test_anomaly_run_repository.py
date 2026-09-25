import pytest
from app.adapters.outbound.persistence.db import create_all_tables, create_db_engine, get_session

@pytest.fixture
def session(tmp_path):
    db_file = tmp_path / "test_runs.db"
    engine = create_db_engine(f"sqlite:///{db_file}")
    create_all_tables(engine)
    with get_session(engine) as session:
        yield session

import pytest
import uuid
from datetime import datetime, timezone
from app.adapters.outbound.persistence.anomaly_run_repository import SqlAlchemyAnomalyRunRepository
from app.domain.models.anomaly_run import AnalysisRun, AnalysisRunStatus

def test_anomaly_run_repository_save_and_get(session):
    repo = SqlAlchemyAnomalyRunRepository(session)
    run_id = str(uuid.uuid4())
    
    run = AnalysisRun(
        id=run_id,
        requested_meter_id="M-101",
        status=AnalysisRunStatus.FAILED,
        started_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, 10, 1, tzinfo=timezone.utc),
        anomalies_detected_count=0,
        error_message="Meter 'M-101' not found"
    )
    
    repo.save(run)
    fetched = repo.get_by_id(run_id)
    
    assert fetched is not None
    assert fetched.id == run_id
    assert fetched.status == AnalysisRunStatus.FAILED
    assert fetched.error_message == "Meter 'M-101' not found"


def test_get_latest_returns_none_when_empty(session):
    repo = SqlAlchemyAnomalyRunRepository(session)
    assert repo.get_latest() is None


def test_get_latest_returns_most_recent_by_finished_at_not_insertion_order(session):
    repo = SqlAlchemyAnomalyRunRepository(session)

    older_run = AnalysisRun(
        id=str(uuid.uuid4()),
        requested_meter_id=None,
        status=AnalysisRunStatus.COMPLETED,
        started_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, 10, 1, tzinfo=timezone.utc),
        anomalies_detected_count=2,
    )
    newer_run = AnalysisRun(
        id=str(uuid.uuid4()),
        requested_meter_id=None,
        status=AnalysisRunStatus.COMPLETED,
        started_at=datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 5, 9, 2, tzinfo=timezone.utc),
        anomalies_detected_count=0,
    )

    # Insertado deliberadamente en orden inverso al cronológico, para
    # probar que get_latest() ordena por finished_at real y no por el
    # orden en que las filas fueron insertadas en la tabla.
    repo.save(newer_run)
    repo.save(older_run)

    latest = repo.get_latest()

    assert latest is not None
    assert latest.id == newer_run.id
    assert latest.finished_at == newer_run.finished_at

