from datetime import datetime
from pydantic import BaseModel

class AnalysisRunRequest(BaseModel):
    meter_id: str | None

class AnalysisRunResponse(BaseModel):
    id: str
    requested_meter_id: str | None
    status: str
    started_at: datetime
    finished_at: datetime
    anomalies_detected_count: int
    error_message: str | None

class DashboardSummaryResponse(BaseModel):
    anomalies_detected: int
    high_priority_count: int
    average_confidence: float | None
    last_analysis_at: datetime | None

class MeterSummaryResponse(BaseModel):
    meter_id: str
    name: str
    status: str
    consumption_kwh: float
    variation_pct: float | None
    anomaly_severity: str | None

class ReadingResponse(BaseModel):
    timestamp: datetime
    consumption_kwh: float
    voltage_v: float
    current_a: float
    power_factor: float
    status: str

class EventResponse(BaseModel):
    event_timestamp: datetime
    event_type: str
    description: str

class MeterDetailResponse(BaseModel):
    meter_id: str
    name: str
    location: str
    status: str
    consumption_kwh: float
    baseline_kwh: float | None
    variation_pct: float | None
    readings: list[ReadingResponse]
    events: list[EventResponse]

class AnomalySummaryResponse(BaseModel):
    id: str
    meter_id: str
    type: str
    severity: str
    confidence: float
    recommended_action: str
    detected_at: datetime

class AnomalyDetailResponse(BaseModel):
    id: str
    meter_id: str
    type: str
    severity: str
    confidence: float
    reason: str
    recommended_action: str
    explanation_source: str
    baseline_kwh: float
    observed_kwh: float
    variation_pct: float
    affected_variables: list[str]
    correlated_event: str | None
    window_start: datetime
    window_end: datetime

class ConsumptionTimelinePointResponse(BaseModel):
    timestamp: datetime
    total_consumption_kwh: float

class ConsumptionTimelineResponse(BaseModel):
    points: list[ConsumptionTimelinePointResponse]
