from fastapi import APIRouter, Depends, HTTPException
from app.adapters.inbound.api.dependencies import get_analyze_meter_use_case

from app.adapters.inbound.api.schemas import AnalysisRunRequest, AnalysisRunResponse
from app.application.analyze_meter import AnalyzeMeterUseCase
from app.domain.models.anomaly_run import AnalysisRunStatus

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/analyze", response_model=AnalysisRunResponse)
def analyze_meter(request: AnalysisRunRequest, use_case: AnalyzeMeterUseCase = Depends(get_analyze_meter_use_case)):
    run = use_case.execute(request.meter_id)
    if run.status == AnalysisRunStatus.FAILED and run.error_message and "not found" in run.error_message.lower():
        raise HTTPException(status_code=404, detail=run.error_message)
    return AnalysisRunResponse(
        id=run.id,
        requested_meter_id=run.requested_meter_id,
        status=run.status.value,
        started_at=run.started_at,
        finished_at=run.finished_at,
        anomalies_detected_count=run.anomalies_detected_count,
        error_message=run.error_message,
    )
