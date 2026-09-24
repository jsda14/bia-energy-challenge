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
from datetime import datetime
from app.adapters.outbound.persistence.anomaly_run_repository import SqlAlchemyAnomalyRunRepository
from app.domain.models.anomaly_run import AnalysisRun, AnalysisRunStatus

def test_anomaly_run_repository_save_and_get(session):
    repo = SqlAlchemyAnomalyRunRepository(session)
    run_id = str(uuid.uuid4())
    
    run = AnalysisRun(
        id=run_id,
        requested_meter_id="M-101",
        status=AnalysisRunStatus.FAILED,
        started_at=datetime(2026, 1, 1, 10, 0),
        finished_at=datetime(2026, 1, 1, 10, 1),
        anomalies_detected_count=0,
        error_message="Meter 'M-101' not found"
    )
    
    repo.save(run)
    fetched = repo.get_by_id(run_id)
    
    assert fetched is not None
    assert fetched.id == run_id
    assert fetched.status == AnalysisRunStatus.FAILED
    assert fetched.error_message == "Meter 'M-101' not found"

