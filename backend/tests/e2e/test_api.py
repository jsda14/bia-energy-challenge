import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.adapters.outbound.persistence.db import create_all_tables
from app.adapters.outbound.persistence.orm_models import Base

@pytest.fixture(scope="module")
def test_engine(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("data") / "test_api.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url)
    create_all_tables(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="module")
def client(test_engine):
    import app.main
    import app.adapters.outbound.persistence.db_state as db_state
    from app.config import Settings
    
    def override_get_settings():
        return Settings(database_url=str(test_engine.url))
    
    original_get_settings = app.main.get_settings
    app.main.get_settings = override_get_settings
    
    original_engine = db_state._engine
    db_state._engine = test_engine
    
    with TestClient(app.main.app) as c:
        yield c
        
    db_state._engine = original_engine
    app.main.get_settings = original_get_settings

def test_cb01_dashboard_summary_no_analysis(client):
    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["anomalies_detected"] == 0
    assert data["high_priority_count"] == 0
    assert data["average_confidence"] is None
    assert data["last_analysis_at"] is None

def test_cb04_analyze_non_existent_meter(client):
    response = client.post("/ai/analyze", json={"meter_id": "M-999"})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_cb03_get_non_existent_meter_detail(client):
    response = client.get("/meters/M-999")
    assert response.status_code == 404

def test_cb05_get_non_existent_anomaly(client):
    response = client.get("/anomalies/123e4567-e89b-12d3-a456-426614174000")
    assert response.status_code == 404

def test_cb06_filters_no_results(client):
    response = client.get("/anomalies?meter_id=M-999")
    assert response.status_code == 200
    assert response.json() == []

    response = client.get("/meters")
    assert response.status_code == 200
    assert response.json() == []

def test_e2e_analyze_all_meters(client, test_engine):
    # Need to insert a meter to test CB-02
    from app.adapters.outbound.persistence.orm_models import MeterORM
    from datetime import datetime
    with sessionmaker(bind=test_engine)() as session:
        session.add(MeterORM(meter_id="M-100", name="Test", location="Loc", status="active", created_at=datetime.utcnow()))
        session.commit()
    
    # CB-02: Meter without readings
    response = client.get("/meters/M-100")
    assert response.status_code == 200
    data = response.json()
    assert data["consumption_kwh"] == 0
    assert data["baseline_kwh"] is None
    assert data["variation_pct"] is None
    assert data["readings"] == []
    
    # Run analysis
    response = client.post("/ai/analyze", json={"meter_id": None})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["anomalies_detected_count"] == 0
