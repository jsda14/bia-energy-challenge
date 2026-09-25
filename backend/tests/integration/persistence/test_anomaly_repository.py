import pytest
from app.adapters.outbound.persistence.db import create_all_tables, create_db_engine, get_session

@pytest.fixture
def session(tmp_path):
    db_file = tmp_path / "test_anomalies.db"
    engine = create_db_engine(f"sqlite:///{db_file}")
    create_all_tables(engine)
    with get_session(engine) as session:
        yield session

import pytest
from datetime import datetime, timezone
from app.adapters.outbound.persistence.anomaly_repository import SqlAlchemyAnomalyRepository
from app.domain.models.anomaly import AnomalyRecord, AnomalyType, Severity, AnomalyEvidence, PersistedAnomaly
from app.domain.ports.ai_explainer_port import AIExplanation

def test_anomaly_repository_save_and_get(session):
    repo = SqlAlchemyAnomalyRepository(session)
    
    ev = AnomalyEvidence(
        baseline_kwh=10.0,
        observed_kwh=20.0,
        variation_pct=100.0,
        affected_variables=["consumption_kwh"],
        correlated_event=None,
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    ar = AnomalyRecord(
        meter_id="M-100",
        detected_at=datetime.now(timezone.utc),
        type=AnomalyType.REAL_ANOMALY,
        severity=Severity.HIGH,
        confidence=0.95,
        evidence=ev
    )
    
    exp = AIExplanation(reason="R", recommended_action="A")
    
    inserted_ids = repo.save_many([(ar, exp)])
    assert len(inserted_ids) == 1
    
    fetched = repo.get_by_id(inserted_ids[0])
    assert fetched is not None
    assert fetched.id == inserted_ids[0]
    assert fetched.reason == "R"
    assert fetched.recommended_action == "A"
    assert fetched.record.meter_id == "M-100"
    assert fetched.record.evidence.variation_pct == 100.0
    assert fetched.record.evidence.affected_variables == ["consumption_kwh"]

def test_anomaly_repository_cb07_double_run(session):
    """Regresión del bug real de duplicación sin límite: el AnomalyDetector
    es determinista, así que una segunda corrida de POST /ai/analyze sobre
    el mismo histórico produce la MISMA ventana (meter_id, type,
    window_start, window_end) para el mismo incidente real. save_many debe
    reconocerla como ya persistida y NO insertarla de nuevo — confirmado
    en producción antes de este fix: 19 filas para un único incidente real
    de M-112 tras varias corridas manuales."""
    repo = SqlAlchemyAnomalyRepository(session)

    ev = AnomalyEvidence(
        baseline_kwh=10.0,
        observed_kwh=20.0,
        variation_pct=100.0,
        affected_variables=["consumption_kwh"],
        correlated_event=None,
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    # Misma ventana en ambas corridas (mismo incidente real) — solo cambia
    # detected_at, que no forma parte de la clave de idempotencia (una
    # misma anomalía puede "detectarse" en momentos distintos sin dejar de
    # ser el mismo incidente).
    ar1 = AnomalyRecord(
        meter_id="M-100",
        detected_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
        type=AnomalyType.REAL_ANOMALY,
        severity=Severity.HIGH,
        confidence=0.95,
        evidence=ev
    )

    ar2 = AnomalyRecord(
        meter_id="M-100",
        detected_at=datetime(2026, 1, 4, tzinfo=timezone.utc),
        type=AnomalyType.REAL_ANOMALY,
        severity=Severity.HIGH,
        confidence=0.95,
        evidence=ev
    )

    exp = AIExplanation(reason="R", recommended_action="A")

    first_run_ids = repo.save_many([(ar1, exp)])
    second_run_ids = repo.save_many([(ar2, exp)])

    assert len(first_run_ids) == 1
    assert len(second_run_ids) == 0  # ya existía, no se insertó de nuevo

    all_anoms = repo.get_by_meter_id("M-100")
    assert len(all_anoms) == 1
    assert all_anoms[0].record.detected_at == datetime(2026, 1, 3, tzinfo=timezone.utc)


def test_anomaly_repository_different_window_is_not_a_duplicate(session):
    """Complemento del test anterior: dos anomalías del mismo medidor y
    tipo pero con ventanas temporales DISTINTAS son incidentes distintos —
    no deben deduplicarse entre sí."""
    repo = SqlAlchemyAnomalyRepository(session)

    def _make(window_start, window_end):
        ev = AnomalyEvidence(
            baseline_kwh=10.0,
            observed_kwh=20.0,
            variation_pct=100.0,
            affected_variables=["consumption_kwh"],
            correlated_event=None,
            window_start=window_start,
            window_end=window_end,
        )
        return AnomalyRecord(
            meter_id="M-100",
            detected_at=datetime.now(timezone.utc),
            type=AnomalyType.REAL_ANOMALY,
            severity=Severity.HIGH,
            confidence=0.95,
            evidence=ev,
        )

    ar1 = _make(datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 1, 2, tzinfo=timezone.utc))
    ar2 = _make(datetime(2026, 2, 1, tzinfo=timezone.utc), datetime(2026, 2, 2, tzinfo=timezone.utc))

    exp = AIExplanation(reason="R", recommended_action="A")
    repo.save_many([(ar1, exp)])
    repo.save_many([(ar2, exp)])

    all_anoms = repo.get_by_meter_id("M-100")
    assert len(all_anoms) == 2


def test_anomaly_repository_exists(session):
    repo = SqlAlchemyAnomalyRepository(session)
    ws = datetime(2026, 1, 1, tzinfo=timezone.utc)
    we = datetime(2026, 1, 2, tzinfo=timezone.utc)

    assert repo.exists("M-100", "REAL_ANOMALY", ws, we) is False

    ev = AnomalyEvidence(
        baseline_kwh=10.0, observed_kwh=20.0, variation_pct=100.0,
        affected_variables=[], correlated_event=None,
        window_start=ws, window_end=we,
    )
    ar = AnomalyRecord(
        meter_id="M-100", detected_at=datetime.now(timezone.utc),
        type=AnomalyType.REAL_ANOMALY, severity=Severity.HIGH,
        confidence=0.9, evidence=ev,
    )
    repo.save_many([(ar, AIExplanation(reason="R", recommended_action="A"))])

    assert repo.exists("M-100", "REAL_ANOMALY", ws, we) is True
    # Otro medidor con la misma ventana no debe dar falso positivo.
    assert repo.exists("M-999", "REAL_ANOMALY", ws, we) is False


def test_update_explanation_returns_false_for_unknown_id(session):
    repo = SqlAlchemyAnomalyRepository(session)
    updated = repo.update_explanation("does-not-exist", AIExplanation(reason="R", recommended_action="A"))
    assert updated is False


def test_update_explanation_replaces_reason_and_action_only(session):
    repo = SqlAlchemyAnomalyRepository(session)

    ev = AnomalyEvidence(
        baseline_kwh=10.0, observed_kwh=20.0, variation_pct=100.0,
        affected_variables=["consumption_kwh"], correlated_event=None,
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    ar = AnomalyRecord(
        meter_id="M-100", detected_at=datetime(2026, 1, 1, 5, tzinfo=timezone.utc),
        type=AnomalyType.REAL_ANOMALY, severity=Severity.HIGH,
        confidence=0.9, evidence=ev,
    )
    inserted_ids = repo.save_many([(ar, AIExplanation(reason="Razón original", recommended_action="Acción original"))])
    anomaly_id = inserted_ids[0]

    updated = repo.update_explanation(
        anomaly_id, AIExplanation(reason="Razón nueva", recommended_action="Acción nueva")
    )
    assert updated is True

    fetched = repo.get_by_id(anomaly_id)
    assert fetched is not None
    assert fetched.reason == "Razón nueva"
    assert fetched.recommended_action == "Acción nueva"
    # Todo lo demás (detección/evidencia) permanece intacto — esto no es
    # una nueva detección, solo una nueva explicación.
    assert fetched.record.type == AnomalyType.REAL_ANOMALY
    assert fetched.record.severity == Severity.HIGH
    assert fetched.record.confidence == 0.9
    assert fetched.record.evidence.variation_pct == 100.0
    assert fetched.record.detected_at == datetime(2026, 1, 1, 5, tzinfo=timezone.utc)

