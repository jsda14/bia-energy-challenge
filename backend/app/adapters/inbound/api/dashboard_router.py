from fastapi import APIRouter, Depends
from app.adapters.inbound.api.dependencies import get_dashboard_summary_use_case

from app.adapters.inbound.api.schemas import DashboardSummaryResponse
from app.application.get_dashboard_summary import GetDashboardSummaryUseCase

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(use_case: GetDashboardSummaryUseCase = Depends(get_dashboard_summary_use_case)):
    dto = use_case.execute()
    return DashboardSummaryResponse.model_validate(dto, from_attributes=True)
