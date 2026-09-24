"""Implementación de AnomalyRepositoryPort mediante SQLAlchemy."""

import uuid
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.adapters.outbound.persistence.db import get_session
from app.adapters.outbound.persistence.orm_models import AnomalyORM
from app.domain.models.anomaly import AnomalyRecord, AnomalyType, Severity, AnomalyEvidence, PersistedAnomaly
from app.domain.ports.ai_explainer_port import AIExplanation
from app.domain.ports.anomaly_repository_port import AnomalyRepositoryPort


class SqlAlchemyAnomalyRepository(AnomalyRepositoryPort):
    """Adaptador de persistencia para anomalías."""

    def __init__(self, session: Session | Engine) -> None:
        if isinstance(session, Engine):
            self._session = get_session(session)
        else:
            self._session = session

    def _to_domain(self, row: AnomalyORM) -> PersistedAnomaly:
        affected_vars = []
        if row.affected_variables:
            affected_vars = [v.strip() for v in row.affected_variables.split(",") if v.strip()]

        evidence = AnomalyEvidence(
            baseline_kwh=row.baseline_kwh,
            observed_kwh=row.observed_kwh,
            variation_pct=row.variation_pct,
            affected_variables=affected_vars,
            correlated_event=row.correlated_event,
            window_start=row.window_start,
            window_end=row.window_end,
        )
        record = AnomalyRecord(
            meter_id=row.meter_id,
            detected_at=row.detected_at,
            type=AnomalyType(row.type),
            severity=Severity(row.severity),
            confidence=row.confidence,
            evidence=evidence,
        )
        return PersistedAnomaly(
            id=row.id,
            record=record,
            reason=row.reason,
            recommended_action=row.recommended_action
        )

    def get_all(self) -> list[PersistedAnomaly]:
        stmt = select(AnomalyORM).order_by(AnomalyORM.detected_at.desc())
        rows = self._session.scalars(stmt).all()
        return [self._to_domain(row) for row in rows]

    def get_by_id(self, anomaly_id: str) -> PersistedAnomaly | None:
        row = self._session.get(AnomalyORM, anomaly_id)
        if not row:
            return None
        return self._to_domain(row)

    def get_by_meter_id(self, meter_id: str) -> list[PersistedAnomaly]:
        stmt = select(AnomalyORM).where(AnomalyORM.meter_id == meter_id).order_by(AnomalyORM.detected_at.desc())
        rows = self._session.scalars(stmt).all()
        return [self._to_domain(row) for row in rows]

    def save_many(self, items: list[tuple[AnomalyRecord, AIExplanation]]) -> list[str]:
        inserted_ids = []
        
        for anomaly, explanation in items:
            new_id = str(uuid.uuid4())
            inserted_ids.append(new_id)
            
            affected_vars_str = ""
            if anomaly.evidence.affected_variables:
                affected_vars_str = ",".join(anomaly.evidence.affected_variables)
                
            new_orm = AnomalyORM(
                id=new_id,
                meter_id=anomaly.meter_id,
                detected_at=anomaly.detected_at,
                type=anomaly.type.value,
                severity=anomaly.severity.value,
                confidence=anomaly.confidence,
                reason=explanation.reason,
                recommended_action=explanation.recommended_action,
                baseline_kwh=anomaly.evidence.baseline_kwh,
                observed_kwh=anomaly.evidence.observed_kwh,
                variation_pct=anomaly.evidence.variation_pct,
                affected_variables=affected_vars_str,
                correlated_event=anomaly.evidence.correlated_event,
                window_start=anomaly.evidence.window_start,
                window_end=anomaly.evidence.window_end,
            )
            self._session.add(new_orm)
            
        self._session.flush()
        return inserted_ids
