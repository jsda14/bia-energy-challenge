from collections import defaultdict
from app.domain.ports.meter_repository_port import MeterRepositoryPort
from app.domain.ports.reading_repository_port import ReadingRepositoryPort
from .dtos import ConsumptionTimelineDTO, ConsumptionTimelinePointDTO

class GetConsumptionTimelineUseCase:
    def __init__(self, meter_repo: MeterRepositoryPort, reading_repo: ReadingRepositoryPort) -> None:
        self.meter_repo = meter_repo
        self.reading_repo = reading_repo

    def execute(self) -> ConsumptionTimelineDTO:
        meters = self.meter_repo.get_all()
        aggregated = defaultdict(float)

        for meter in meters:
            readings = self.reading_repo.get_by_meter_id(meter.meter_id)
            for r in readings:
                aggregated[r.timestamp] += r.consumption_kwh

        points = [
            ConsumptionTimelinePointDTO(timestamp=ts, total_consumption_kwh=round(kwh, 2))
            for ts, kwh in sorted(aggregated.items())
        ]

        return ConsumptionTimelineDTO(points=points)
