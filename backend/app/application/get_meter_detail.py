from app.application.dtos import MeterDetailDTO, ReadingDTO, EventDTO
from app.domain.ports.meter_repository_port import MeterRepositoryPort
from app.domain.ports.reading_repository_port import ReadingRepositoryPort
from app.domain.ports.anomaly_repository_port import AnomalyRepositoryPort
from app.domain.ports.event_repository_port import EventRepositoryPort

class GetMeterDetailUseCase:
    def __init__(
        self,
        meter_repo: MeterRepositoryPort,
        reading_repo: ReadingRepositoryPort,
        anomaly_repo: AnomalyRepositoryPort,
        event_repo: EventRepositoryPort,
    ) -> None:
        self.meter_repo = meter_repo
        self.reading_repo = reading_repo
        self.anomaly_repo = anomaly_repo
        self.event_repo = event_repo

    def execute(self, meter_id: str) -> MeterDetailDTO | None:
        m = self.meter_repo.get_by_meter_id(meter_id)
        if not m:
            return None
            
        readings = self.reading_repo.get_by_meter_id(meter_id)
        anomalies = self.anomaly_repo.get_by_meter_id(meter_id)
        
        consumption_kwh = sum(r.consumption_kwh for r in readings) if readings else 0.0
        
        status = "OK"
        if any(a.record.severity.value == "HIGH" for a in anomalies):
            status = "Critical"
        elif any(a.record.severity.value == "MEDIUM" for a in anomalies):
            status = "Alert"
            
        baseline_kwh = None
        variation_pct = None
        if anomalies:
            recent_ev = anomalies[0].record.evidence
            baseline_kwh = recent_ev.baseline_kwh
            variation_pct = recent_ev.variation_pct
            
        reading_dtos = [
            ReadingDTO(
                timestamp=r.timestamp,
                consumption_kwh=r.consumption_kwh,
                voltage_v=r.voltage_v,
                current_a=r.current_a,
                power_factor=r.power_factor,
                status=r.status,
            )
            for r in readings
        ]
        
        events = self.event_repo.get_by_meter_id(meter_id)
        event_dtos = [
            EventDTO(
                event_timestamp=e.event_timestamp,
                event_type=e.event_type,
                description=e.description,
            )
            for e in events
        ]
        
        return MeterDetailDTO(
            meter_id=m.meter_id,
            name=m.name,
            location=m.location,
            status=status,
            consumption_kwh=consumption_kwh,
            baseline_kwh=baseline_kwh,
            variation_pct=variation_pct,
            readings=reading_dtos,
            events=event_dtos,
        )
