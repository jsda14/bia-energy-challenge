"""Tests de integración para el script de seed (RN-03, RN-04, CB-01, CB-04, CB-05)."""

from datetime import datetime
from pathlib import Path
import pytest

from app.adapters.outbound.persistence.db import (
    create_all_tables,
    create_db_engine,
    get_session,
)
from app.adapters.outbound.persistence.event_repository import (
    SqlAlchemyEventRepository,
)
from app.adapters.outbound.persistence.meter_repository import (
    SqlAlchemyMeterRepository,
)
from app.adapters.outbound.persistence.reading_repository import (
    SqlAlchemyReadingRepository,
)
from app.domain.models.event import EventType
from scripts.seed_data import (
    derive_meters,
    load_events_csv,
    load_readings_csv,
    seed,
)


@pytest.fixture
def repo_root():
    """Ruta a la raíz del repositorio donde se encuentran readings.csv y events.csv."""
    return Path(__file__).resolve().parents[3]


def test_cb01_malformed_readings_csv_raises_value_error(tmp_path):
    """Valida CB-01: un valor float no convertible lanza ValueError detallando archivo y línea."""
    bad_csv = tmp_path / "bad_readings.csv"
    bad_csv.write_text(
        "meter_id,timestamp,consumption_kwh,voltage_v,current_a,power_factor,status\n"
        "M-101,2026-09-01 00:00:00,NOT_A_FLOAT,220.0,15.0,0.95,OK\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Error parsing.*bad_readings.csv.*line 2"):
        load_readings_csv(str(bad_csv))


def test_cb01_malformed_events_csv_raises_value_error(tmp_path):
    """Valida CB-01: un tipo de evento inválido en events.csv lanza ValueError con archivo y línea."""
    bad_csv = tmp_path / "bad_events.csv"
    bad_csv.write_text(
        "meter_id,event_timestamp,event_type,description\n"
        "M-101,2026-09-01 00:00:00,INVALID_EVENT_TYPE,Some event\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Error parsing.*bad_events.csv.*line 2"):
        load_events_csv(str(bad_csv))


def test_derive_meters_synthesizes_expected_fields():
    """Valida RN-03: síntesis de medidores únicos a partir de readings."""
    reading_rows = [
        {
            "meter_id": "M-101",
            "timestamp": datetime(2026, 9, 1, 10, 0),
            "consumption_kwh": 20.0,
            "voltage_v": 220.0,
            "current_a": 10.0,
            "power_factor": 0.9,
            "status": "OK",
        },
        {
            "meter_id": "M-101",
            "timestamp": datetime(2026, 9, 1, 8, 0),  # Más temprano
            "consumption_kwh": 15.0,
            "voltage_v": 220.0,
            "current_a": 10.0,
            "power_factor": 0.9,
            "status": "OK",
        },
        {
            "meter_id": "M-102",
            "timestamp": datetime(2026, 9, 1, 9, 0),
            "consumption_kwh": 30.0,
            "voltage_v": 220.0,
            "current_a": 15.0,
            "power_factor": 0.95,
            "status": "OK",
        },
    ]

    meters = derive_meters(reading_rows)
    assert len(meters) == 2

    m101 = next(m for m in meters if m["meter_id"] == "M-101")
    assert m101["name"] == "M-101"
    assert m101["location"] == "Unknown"
    assert m101["status"] == "active"
    assert m101["created_at"] == datetime(2026, 9, 1, 8, 0)

    m102 = next(m for m in meters if m["meter_id"] == "M-102")
    assert m102["name"] == "M-102"
    assert m102["created_at"] == datetime(2026, 9, 1, 9, 0)


def test_seed_real_data_and_idempotency(tmp_path, repo_root):
    """Valida seed completo contra datos reales y prueba estricta de idempotencia (RN-04, CB-04)."""
    readings_csv = str(repo_root / "readings.csv")
    events_csv = str(repo_root / "events.csv")
    db_file = tmp_path / "test_seed.db"
    db_url = f"sqlite:///{db_file}"

    # Primera corrida del seed
    seed(readings_csv, events_csv, db_url)

    engine = create_db_engine(db_url)
    session = get_session(engine)
    m_repo = SqlAlchemyMeterRepository(session)
    r_repo = SqlAlchemyReadingRepository(session)
    e_repo = SqlAlchemyEventRepository(session)

    meters_1 = m_repo.get_all()
    events_1 = e_repo.get_all()
    total_readings_1 = sum(
        len(r_repo.get_by_meter_id(m.meter_id)) for m in meters_1
    )

    assert len(meters_1) == 12
    assert total_readings_1 == 4032
    assert len(events_1) == 4
    session.close()

    # Segunda corrida del seed sobre la MISMA base de datos (CB-04)
    seed(readings_csv, events_csv, db_url)

    session2 = get_session(engine)
    m_repo2 = SqlAlchemyMeterRepository(session2)
    r_repo2 = SqlAlchemyReadingRepository(session2)
    e_repo2 = SqlAlchemyEventRepository(session2)

    meters_2 = m_repo2.get_all()
    events_2 = e_repo2.get_all()
    total_readings_2 = sum(
        len(r_repo2.get_by_meter_id(m.meter_id)) for m in meters_2
    )

    # Conteos EXACTAMENTE iguales
    assert len(meters_2) == 12
    assert total_readings_2 == 4032
    assert len(events_2) == 4
    session2.close()


def test_cb05_create_all_tables_preserves_existing_data(tmp_path):
    """Valida CB-05: llamar create_all_tables sobre una base poblada preserva los datos existentes."""
    db_file = tmp_path / "test_preserve.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_db_engine(db_url)
    create_all_tables(engine)

    session = get_session(engine)
    m_repo = SqlAlchemyMeterRepository(session)
    from app.domain.models.meter import Meter

    m_repo.save(
        Meter(
            id="M-101",
            meter_id="M-101",
            name="M-101",
            location="Loc",
            status="active",
        )
    )
    session.close()

    # Volver a invocar create_all_tables
    create_all_tables(engine)

    session2 = get_session(engine)
    m_repo2 = SqlAlchemyMeterRepository(session2)
    meters = m_repo2.get_all()
    assert len(meters) == 1
    assert meters[0].meter_id == "M-101"
    session2.close()
