"""Implementación de AnomalyRunRepositoryPort mediante SQLAlchemy."""

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.adapters.outbound.persistence.db import get_session
from app.adapters.outbound.persistence.orm_models import AnalysisRunORM
from app.domain.models.anomaly_run import AnalysisRun, AnalysisRunStatus
from app.domain.ports.anomaly_run_repository_port import AnomalyRunRepositoryPort


class SqlAlchemyAnomalyRunRepository(AnomalyRunRepositoryPort):
    """Adaptador de persistencia para ejecuciones de análisis."""

    def __init__(self, session: Session | Engine) -> None:
        if isinstance(session, Engine):
            self._session = get_session(session)
        else:
            self._session = session

    def save(self, run: AnalysisRun) -> None:
        new_orm = AnalysisRunORM(
            id=run.id,
            requested_meter_id=run.requested_meter_id,
            status=run.status.value,
            started_at=run.started_at,
            finished_at=run.finished_at,
            anomalies_detected_count=run.anomalies_detected_count,
            error_message=run.error_message,
        )
        self._session.add(new_orm)
        self._session.flush()

    def get_by_id(self, run_id: str) -> AnalysisRun | None:
        row = self._session.get(AnalysisRunORM, run_id)
        if not row:
            return None
        return self._to_domain(row)

    def get_latest(self) -> AnalysisRun | None:
        stmt = select(AnalysisRunORM).order_by(AnalysisRunORM.finished_at.desc()).limit(1)
        row = self._session.scalars(stmt).first()
        if not row:
            return None
        return self._to_domain(row)

    def _to_domain(self, row: AnalysisRunORM) -> AnalysisRun:
        return AnalysisRun(
            id=row.id,
            requested_meter_id=row.requested_meter_id,
            status=AnalysisRunStatus(row.status),
            started_at=row.started_at,
            finished_at=row.finished_at,
            anomalies_detected_count=row.anomalies_detected_count,
            error_message=row.error_message,
        )
