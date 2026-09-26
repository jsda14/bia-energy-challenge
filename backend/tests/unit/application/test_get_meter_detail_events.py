import pytest
from datetime import datetime, timezone
from app.application.get_meter_detail import GetMeterDetailUseCase
from app.domain.models.meter import Meter
from app.domain.models.event import Event

class DummyMeterRepo:
    def __init__(self, meter):
        self.meter = meter
    def get_by_meter_id(self, meter_id):
        return self.meter if self.meter and self.meter.meter_id == meter_id else None

class DummyReadingRepo:
    def get_by_meter_id(self, meter_id):
        return []

class DummyAnomalyRepo:
    def get_by_meter_id(self, meter_id):
        return []

class DummyEventRepo:
    def __init__(self, events):
        self.events = events
    def get_by_meter_id(self, meter_id):
        return [e for e in self.events if e.meter_id == meter_id]

def test_get_meter_detail_with_events():
    m1 = Meter(id="id1", meter_id="m1", name="M1", location="L", status="active")
    t1 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    ev = Event(meter_id="m1", event_timestamp=t1, event_type="OPERATIONAL_CHANGE", description="desc")
    
    meter_repo = DummyMeterRepo(m1)
    reading_repo = DummyReadingRepo()
    anomaly_repo = DummyAnomalyRepo()
    event_repo = DummyEventRepo([ev])
    
    use_case = GetMeterDetailUseCase(meter_repo, reading_repo, anomaly_repo, event_repo)
    dto = use_case.execute("m1")
    
    assert dto is not None
    assert len(dto.events) == 1
    assert dto.events[0].event_type == "OPERATIONAL_CHANGE"
    assert dto.events[0].description == "desc"

def test_get_meter_detail_no_events():
    m1 = Meter(id="id1", meter_id="m1", name="M1", location="L", status="active")
    meter_repo = DummyMeterRepo(m1)
    use_case = GetMeterDetailUseCase(meter_repo, DummyReadingRepo(), DummyAnomalyRepo(), DummyEventRepo([]))
    dto = use_case.execute("m1")
    
    assert dto is not None
    assert len(dto.events) == 0
