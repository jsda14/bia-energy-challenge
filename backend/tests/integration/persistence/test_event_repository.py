"""Tests de integración para SqlAlchemyEventRepository (RN-01, RN-04)."""

from datetime import datetime, timezone
import pytest
from app.adapters.outbound.persistence.db import (
    create_all_tables,
    create_db_engine,
    get_session,
)
from app.adapters.outbound.persistence.event_repository import (
    SqlAlchemyEventRepository,
)
from app.domain.models.event import Event, EventType


@pytest.fixture
def session(tmp_path):
    """Crea una base de datos SQLite temporal y entrega una sesión."""
    db_file = tmp_path / "test_events.db"
    engine = create_db_engine(f"sqlite:///{db_file}")
    create_all_tables(engine)
    sess = get_session(engine)
    try:
        yield sess
    finally:
        sess.close()


def test_get_by_meter_id_empty(session):
    """Valida que un medidor sin eventos retorne lista vacía."""
    repo = SqlAlchemyEventRepository(session)
    assert repo.get_by_meter_id("M-NO-EVENTS") == []


def test_save_many_and_get_all_ordered(session):
    """Valida persistencia y ordenamiento cronológico de eventos."""
    repo = SqlAlchemyEventRepository(session)
    t1 = datetime(2026, 9, 2, 8, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 5, 14, 0, tzinfo=timezone.utc)

    events = [
        Event(
            meter_id="M-104",
            event_timestamp=t2,
            event_type=EventType.OPERATIONAL_CHANGE,
            description="Cambio de turno tarde",
        ),
        Event(
            meter_id="M-106",
            event_timestamp=t1,
            event_type=EventType.SCHEDULED_OUTAGE,
            description="Mantenimiento preventivo",
        ),
    ]

    repo.save_many(events)

    all_events = repo.get_all()
    assert len(all_events) == 2
    assert all_events[0].meter_id == "M-106"
    assert all_events[0].event_timestamp == t1
    assert all_events[0].event_type == EventType.SCHEDULED_OUTAGE
    assert all_events[1].meter_id == "M-104"
    assert all_events[1].event_timestamp == t2
    assert all_events[1].event_type == EventType.OPERATIONAL_CHANGE


def test_get_by_meter_id_filters_correctly(session):
    """Valida que get_by_meter_id filtre únicamente los eventos del medidor indicado."""
    repo = SqlAlchemyEventRepository(session)
    events = [
        Event(
            meter_id="M-104",
            event_timestamp=datetime(2026, 9, 5, 14, 0, tzinfo=timezone.utc),
            event_type=EventType.OPERATIONAL_CHANGE,
            description="Línea nueva",
        ),
        Event(
            meter_id="M-106",
            event_timestamp=datetime(2026, 9, 2, 8, 0, tzinfo=timezone.utc),
            event_type=EventType.SCHEDULED_OUTAGE,
            description="Mantenimiento",
        ),
    ]
    repo.save_many(events)

    m104_events = repo.get_by_meter_id("M-104")
    assert len(m104_events) == 1
    assert m104_events[0].meter_id == "M-104"
    assert m104_events[0].description == "Línea nueva"


def test_save_many_idempotency(session):
    """Valida RN-04: guardar eventos idénticos (meter_id, timestamp, type) no duplica."""
    repo = SqlAlchemyEventRepository(session)
    event = Event(
        meter_id="M-104",
        event_timestamp=datetime(2026, 9, 5, 14, 0, tzinfo=timezone.utc),
        event_type=EventType.OPERATIONAL_CHANGE,
        description="Línea nueva",
    )
    repo.save_many([event])
    repo.save_many([event])

    all_events = repo.get_all()
    assert len(all_events) == 1
