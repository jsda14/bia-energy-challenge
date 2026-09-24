from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.adapters.outbound.persistence.db import create_all_tables
from app.adapters.outbound.persistence.db_state import get_or_create_engine
from app.adapters.outbound.persistence.meter_repository import SqlAlchemyMeterRepository
from app.adapters.outbound.persistence.reading_repository import SqlAlchemyReadingRepository
from app.adapters.outbound.persistence.event_repository import SqlAlchemyEventRepository
from app.adapters.outbound.persistence.anomaly_repository import SqlAlchemyAnomalyRepository
from app.adapters.outbound.persistence.anomaly_run_repository import SqlAlchemyAnomalyRunRepository
from app.adapters.outbound.ai.template_explainer_adapter import TemplateExplainerAdapter
from app.domain.detection.detector import AnomalyDetector

from app.application.analyze_meter import AnalyzeMeterUseCase
from app.application.get_dashboard_summary import GetDashboardSummaryUseCase
from app.application.list_meters import ListMetersUseCase
from app.application.get_meter_detail import GetMeterDetailUseCase
from app.application.list_anomalies import ListAnomaliesUseCase
from app.application.get_anomaly_detail import GetAnomalyDetailUseCase

from app.adapters.inbound.api import meters_router, anomalies_router, dashboard_router, ai_router
from app.adapters.inbound.api.dependencies import (
    get_db_session,
    get_analyze_meter_use_case as stub_analyze,
    get_dashboard_summary_use_case as stub_dash,
    get_list_meters_use_case as stub_list_meters,
    get_meter_detail_use_case as stub_meter_detail,
    get_list_anomalies_use_case as stub_list_anom,
    get_anomaly_detail_use_case as stub_anom_detail
)

app = FastAPI(title="Bia Energy Challenge API")

@app.on_event("startup")
def startup_event():
    engine = get_or_create_engine()
    create_all_tables(engine)

from app.adapters.outbound.ai.claude_explainer_adapter import ClaudeExplainerAdapter
from app.domain.ports.ai_explainer_port import AIExplainerPort

def get_explainer(session: Session) -> AIExplainerPort:
    settings = get_settings()
    if settings.anthropic_api_key:
        event_repo = SqlAlchemyEventRepository(session)
        return ClaudeExplainerAdapter(
            event_repo=event_repo,
            api_key=settings.anthropic_api_key,
            model=settings.claude_model
        )
    return TemplateExplainerAdapter()

def get_detector() -> AnomalyDetector:
    return AnomalyDetector()

def build_analyze_use_case(session: Session = Depends(get_db_session)) -> AnalyzeMeterUseCase:
    return AnalyzeMeterUseCase(
        meter_repo=SqlAlchemyMeterRepository(session),
        reading_repo=SqlAlchemyReadingRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
        anomaly_repo=SqlAlchemyAnomalyRepository(session),
        run_repo=SqlAlchemyAnomalyRunRepository(session),
        explainer=get_explainer(session),
        detector=get_detector(),
    )
    
def build_dashboard_summary_use_case(session: Session = Depends(get_db_session)) -> GetDashboardSummaryUseCase:
    return GetDashboardSummaryUseCase(
        meter_repo=SqlAlchemyMeterRepository(session),
        anomaly_repo=SqlAlchemyAnomalyRepository(session),
        run_repo=SqlAlchemyAnomalyRunRepository(session),
    )

def build_list_meters_use_case(session: Session = Depends(get_db_session)) -> ListMetersUseCase:
    return ListMetersUseCase(
        meter_repo=SqlAlchemyMeterRepository(session),
        reading_repo=SqlAlchemyReadingRepository(session),
        anomaly_repo=SqlAlchemyAnomalyRepository(session),
    )

def build_meter_detail_use_case(session: Session = Depends(get_db_session)) -> GetMeterDetailUseCase:
    return GetMeterDetailUseCase(
        meter_repo=SqlAlchemyMeterRepository(session),
        reading_repo=SqlAlchemyReadingRepository(session),
        anomaly_repo=SqlAlchemyAnomalyRepository(session),
    )

def build_list_anomalies_use_case(session: Session = Depends(get_db_session)) -> ListAnomaliesUseCase:
    return ListAnomaliesUseCase(anomaly_repo=SqlAlchemyAnomalyRepository(session))

def build_anomaly_detail_use_case(session: Session = Depends(get_db_session)) -> GetAnomalyDetailUseCase:
    return GetAnomalyDetailUseCase(anomaly_repo=SqlAlchemyAnomalyRepository(session))

# Dependency Injection overrides for routers
app.dependency_overrides[stub_analyze] = build_analyze_use_case
app.dependency_overrides[stub_dash] = build_dashboard_summary_use_case
app.dependency_overrides[stub_list_meters] = build_list_meters_use_case
app.dependency_overrides[stub_meter_detail] = build_meter_detail_use_case
app.dependency_overrides[stub_list_anom] = build_list_anomalies_use_case
app.dependency_overrides[stub_anom_detail] = build_anomaly_detail_use_case

app.include_router(meters_router)
app.include_router(anomalies_router)
app.include_router(dashboard_router)
app.include_router(ai_router)
