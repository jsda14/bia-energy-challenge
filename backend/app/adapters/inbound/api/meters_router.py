from fastapi import APIRouter, Depends, HTTPException
from app.adapters.inbound.api.dependencies import get_list_meters_use_case, get_meter_detail_use_case

from app.adapters.inbound.api.schemas import MeterSummaryResponse, MeterDetailResponse
from app.application.list_meters import ListMetersUseCase
from app.application.get_meter_detail import GetMeterDetailUseCase

router = APIRouter(prefix="/meters", tags=["Meters"])

@router.get("", response_model=list[MeterSummaryResponse])
def list_meters(use_case: ListMetersUseCase = Depends(get_list_meters_use_case)):
    dtos = use_case.execute()
    return [MeterSummaryResponse.model_validate(d, from_attributes=True) for d in dtos]

@router.get("/{meter_id}", response_model=MeterDetailResponse)
def get_meter_detail(meter_id: str, use_case: GetMeterDetailUseCase = Depends(get_meter_detail_use_case)):
    dto = use_case.execute(meter_id)
    if not dto:
        raise HTTPException(status_code=404, detail="Meter not found")
    return MeterDetailResponse.model_validate(dto, from_attributes=True)
