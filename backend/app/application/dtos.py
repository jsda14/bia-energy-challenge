from dataclasses import dataclass
from datetime import datetime

@dataclass
class DashboardSummaryDTO:
    anomalies_detected: int
    high_priority_count: int
    average_confidence: float | None
    last_analysis_at: datetime | None

@dataclass
class MeterSummaryDTO:
    meter_id: str
    name: str
    status: str
    consumption_kwh: float
    variation_pct: float | None
    anomaly_severity: str | None

@dataclass
class ReadingDTO:
    timestamp: datetime
    consumption_kwh: float
    voltage_v: float
    current_a: float
    power_factor: float
    status: str

@dataclass
class MeterDetailDTO:
    meter_id: str
    name: str
    location: str
    status: str
    consumption_kwh: float
    baseline_kwh: float | None
    variation_pct: float | None
    readings: list[ReadingDTO]

@dataclass
class AnomalySummaryDTO:
    id: str
    meter_id: str
    type: str
    severity: str
    confidence: float
    recommended_action: str
    detected_at: datetime

@dataclass
class AnomalyDetailDTO:
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
