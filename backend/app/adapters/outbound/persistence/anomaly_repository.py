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
            recommended_action=row.recommended_action,
            explanation_source=row.explanation_source,
            triage_status=row.triage_status,
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

    def update_explanation(self, anomaly_id: str, explanation: AIExplanation) -> bool:
        row = self._session.get(AnomalyORM, anomaly_id)
        if not row:
            return False
        row.reason = explanation.reason
        row.recommended_action = explanation.recommended_action
        row.explanation_source = explanation.source
        self._session.flush()
        return True

    def update_triage_status(self, anomaly_id: str, triage_status: str) -> bool:
        row = self._session.get(AnomalyORM, anomaly_id)
        if not row:
            return False
        row.triage_status = triage_status
        self._session.flush()
        return True

    def exists(self, meter_id: str, anomaly_type: str, window_start, window_end) -> bool:
        stmt = select(AnomalyORM.id).where(
            AnomalyORM.meter_id == meter_id,
            AnomalyORM.type == anomaly_type,
            AnomalyORM.window_start == window_start,
            AnomalyORM.window_end == window_end,
        )
        return self._session.scalars(stmt).first() is not None

    def save_many(self, items: list[tuple[AnomalyRecord, AIExplanation]]) -> list[str]:
        """Inserta anomalías en bloque de forma idempotente por
        (meter_id, type, window_start, window_end).

        El `AnomalyDetector` es determinista: sobre el mismo histórico de
        lecturas/eventos, dos corridas de `POST /ai/analyze` producen
        exactamente la misma ventana temporal para el mismo incidente real.
        Sin esta idempotencia, cada corrida duplicaba las anomalías ya
        detectadas (confirmado en producción: 19 filas para un único
        incidente real de M-112 tras varias corridas) — infla el Dashboard
        y la tabla de Anomalías sin aportar información nueva. Si ya existe
        una anomalía con esa combinación exacta, no se re-inserta (se omite
        de `inserted_ids`, ya que no hay una fila nueva que referenciar).
        """
        if not items:
            return []

        meter_ids = {anomaly.meter_id for anomaly, _ in items}
        existing_stmt = select(
            AnomalyORM.meter_id, AnomalyORM.type, AnomalyORM.window_start, AnomalyORM.window_end
        ).where(AnomalyORM.meter_id.in_(meter_ids))
        existing_keys = set(self._session.execute(existing_stmt).all())

        seen = set(existing_keys)
        inserted_ids: list[str] = []

        for anomaly, explanation in items:
            key = (anomaly.meter_id, anomaly.type.value, anomaly.evidence.window_start, anomaly.evidence.window_end)
            if key in seen:
                continue
            seen.add(key)

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
                explanation_source=explanation.source,
                triage_status="NEW",
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
