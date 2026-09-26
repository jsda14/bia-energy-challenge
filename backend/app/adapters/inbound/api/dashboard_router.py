from fastapi import APIRouter, Depends
from app.adapters.inbound.api.dependencies import get_dashboard_summary_use_case, get_consumption_timeline_use_case

from app.adapters.inbound.api.schemas import DashboardSummaryResponse, ConsumptionTimelineResponse
from app.application.get_dashboard_summary import GetDashboardSummaryUseCase
from app.application.get_consumption_timeline import GetConsumptionTimelineUseCase

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(use_case: GetDashboardSummaryUseCase = Depends(get_dashboard_summary_use_case)):
    dto = use_case.execute()
    return DashboardSummaryResponse.model_validate(dto, from_attributes=True)

@router.get("/consumption-timeline", response_model=ConsumptionTimelineResponse)
def get_consumption_timeline(use_case: GetConsumptionTimelineUseCase = Depends(get_consumption_timeline_use_case)):
    dto = use_case.execute()
    return ConsumptionTimelineResponse.model_validate(dto, from_attributes=True)
