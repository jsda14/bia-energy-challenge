"""Tests de integración para SqlAlchemyReadingRepository (RN-01, RN-04, CB-02, CB-03)."""

from datetime import datetime, timedelta, timezone
import pytest
from app.adapters.outbound.persistence.db import (
    create_all_tables,
    create_db_engine,
    get_session,
)
from app.adapters.outbound.persistence.reading_repository import (
    SqlAlchemyReadingRepository,
)
from app.domain.models.reading import Reading


@pytest.fixture
def session(tmp_path):
    """Crea una base de datos SQLite temporal y entrega una sesión."""
    db_file = tmp_path / "test_readings.db"
    engine = create_db_engine(f"sqlite:///{db_file}")
    create_all_tables(engine)
    sess = get_session(engine)
    try:
        yield sess
    finally:
        sess.close()


def test_get_by_meter_id_empty_returns_empty_list(session):
    """Valida CB-02: medidor sin lecturas o inexistente retorna lista vacía."""
    repo = SqlAlchemyReadingRepository(session)
    assert repo.get_by_meter_id("M-UNKNOWN") == []


def test_save_many_and_get_by_meter_id_ordered(session):
    """Valida persistencia y ordenamiento ascendente por timestamp (RN-01)."""
    repo = SqlAlchemyReadingRepository(session)
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 9, 1, 11, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

    # Insertamos desordenadas intencionalmente
    readings = [
        Reading(
            meter_id="M-101",
            timestamp=t2,
            consumption_kwh=30.0,
            voltage_v=220.0,
            current_a=15.0,
            power_factor=0.95,
            status="OK",
        ),
        Reading(
            meter_id="M-101",
            timestamp=t0,
            consumption_kwh=10.0,
            voltage_v=220.0,
            current_a=15.0,
            power_factor=0.95,
            status="OK",
        ),
        Reading(
            meter_id="M-101",
            timestamp=t1,
            consumption_kwh=20.0,
            voltage_v=220.0,
            current_a=15.0,
            power_factor=0.95,
            status="OK",
        ),
    ]

    repo.save_many(readings)

    results = repo.get_by_meter_id("M-101")
    assert len(results) == 3
    assert all(isinstance(r, Reading) for r in results)
    assert [r.timestamp for r in results] == [t0, t1, t2]
    assert [r.consumption_kwh for r in results] == [10.0, 20.0, 30.0]


def test_get_by_meter_id_and_range(session):
    """Valida filtrado inclusivo por rango [start, end]."""
    repo = SqlAlchemyReadingRepository(session)
    base_ts = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)

    readings = [
        Reading(
            meter_id="M-101",
            timestamp=base_ts + timedelta(hours=i),
            consumption_kwh=float(i),
            voltage_v=220.0,
            current_a=10.0,
            power_factor=0.9,
            status="OK",
        )
        for i in range(10)
    ]
    repo.save_many(readings)

    start = base_ts + timedelta(hours=3)
    end = base_ts + timedelta(hours=6)
    in_range = repo.get_by_meter_id_and_range("M-101", start, end)

    assert len(in_range) == 4
    assert in_range[0].timestamp == start
    assert in_range[-1].timestamp == end


def test_get_by_meter_id_and_range_empty(session):
    """Valida CB-03: rango sin intersección retorna lista vacía."""
    repo = SqlAlchemyReadingRepository(session)
    base_ts = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
    readings = [
        Reading(
            meter_id="M-101",
            timestamp=base_ts,
            consumption_kwh=10.0,
            voltage_v=220.0,
            current_a=10.0,
            power_factor=0.9,
            status="OK",
        )
    ]
    repo.save_many(readings)

    out_start = base_ts + timedelta(days=5)
    out_end = base_ts + timedelta(days=6)
    assert repo.get_by_meter_id_and_range("M-101", out_start, out_end) == []


def test_save_many_idempotency(session):
    """Valida RN-04: save_many duplicando (meter_id, timestamp) no crea duplicados ni lanza excepción."""
    repo = SqlAlchemyReadingRepository(session)
    ts = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)

    r1 = Reading(
        meter_id="M-101",
        timestamp=ts,
        consumption_kwh=15.0,
        voltage_v=220.0,
        current_a=10.0,
        power_factor=0.95,
        status="OK",
    )
    repo.save_many([r1])

    # Guardar exactamente la misma lectura nuevamente
    repo.save_many([r1])

    results = repo.get_by_meter_id("M-101")
    assert len(results) == 1
