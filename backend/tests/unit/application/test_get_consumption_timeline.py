import pytest
from datetime import datetime, timezone
from app.application.get_consumption_timeline import GetConsumptionTimelineUseCase
from app.domain.models.meter import Meter
from app.domain.models.reading import Reading

class DummyMeterRepo:
    def __init__(self, meters):
        self.meters = meters
    def get_all(self):
        return self.meters

class DummyReadingRepo:
    def __init__(self, readings_by_meter):
        self.readings_by_meter = readings_by_meter
    def get_by_meter_id(self, meter_id):
        return self.readings_by_meter.get(meter_id, [])

def test_get_consumption_timeline_aggregates_correctly():
    m1 = Meter(id="id1", meter_id="m1", name="M1", location="L", status="active")
    m2 = Meter(id="id2", meter_id="m2", name="M2", location="L", status="active")
    
    t1 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc)
    
    # Meter 1 readings
    r1 = Reading(timestamp=t1, meter_id="m1", consumption_kwh=10.0, voltage_v=0, current_a=0, power_factor=0, status="OK")
    r2 = Reading(timestamp=t2, meter_id="m1", consumption_kwh=20.0, voltage_v=0, current_a=0, power_factor=0, status="OK")
    
    # Meter 2 readings
    r3 = Reading(timestamp=t1, meter_id="m2", consumption_kwh=5.5, voltage_v=0, current_a=0, power_factor=0, status="OK")
    # Missing t2 for m2 just to test partial logic
    
    meter_repo = DummyMeterRepo([m1, m2])
    reading_repo = DummyReadingRepo({
        "m1": [r1, r2],
        "m2": [r3],
    })
    
    use_case = GetConsumptionTimelineUseCase(meter_repo, reading_repo)
    dto = use_case.execute()
    
    assert len(dto.points) == 2
    
    # Both points are aggregated
    assert dto.points[0].timestamp == t1
    assert dto.points[0].total_consumption_kwh == 15.5
    
    # Only m1 has data for t2
    assert dto.points[1].timestamp == t2
    assert dto.points[1].total_consumption_kwh == 20.0

def test_get_consumption_timeline_empty():
    meter_repo = DummyMeterRepo([])
    reading_repo = DummyReadingRepo({})
    use_case = GetConsumptionTimelineUseCase(meter_repo, reading_repo)
    dto = use_case.execute()
    assert len(dto.points) == 0
