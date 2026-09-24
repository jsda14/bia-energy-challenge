from fastapi import APIRouter, Depends, HTTPException
from app.adapters.inbound.api.dependencies import get_list_anomalies_use_case, get_anomaly_detail_use_case

from app.adapters.inbound.api.schemas import AnomalySummaryResponse, AnomalyDetailResponse
from app.application.list_anomalies import ListAnomaliesUseCase
from app.application.get_anomaly_detail import GetAnomalyDetailUseCase

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])

@router.get("", response_model=list[AnomalySummaryResponse])
def list_anomalies(meter_id: str | None = None, use_case: ListAnomaliesUseCase = Depends(get_list_anomalies_use_case)):
    dtos = use_case.execute(meter_id)
    return [AnomalySummaryResponse.model_validate(d, from_attributes=True) for d in dtos]

@router.get("/{anomaly_id}", response_model=AnomalyDetailResponse)
def get_anomaly_detail(anomaly_id: str, use_case: GetAnomalyDetailUseCase = Depends(get_anomaly_detail_use_case)):
    dto = use_case.execute(anomaly_id)
    if not dto:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return AnomalyDetailResponse.model_validate(dto, from_attributes=True)
