"""Tests de integración para SqlAlchemyMeterRepository (RN-01, RN-04)."""

import pytest
from app.adapters.outbound.persistence.db import (
    create_all_tables,
    create_db_engine,
    get_session,
)
from app.adapters.outbound.persistence.meter_repository import (
    SqlAlchemyMeterRepository,
)
from app.domain.models.meter import Meter


@pytest.fixture
def session(tmp_path):
    """Crea una base de datos SQLite temporal y entrega una sesión."""
    db_file = tmp_path / "test_meters.db"
    engine = create_db_engine(f"sqlite:///{db_file}")
    create_all_tables(engine)
    sess = get_session(engine)
    try:
        yield sess
    finally:
        sess.close()


def test_get_all_empty(session):
    """Valida que get_all retorne lista vacía cuando no hay medidores."""
    repo = SqlAlchemyMeterRepository(session)
    assert repo.get_all() == []


def test_save_and_get_by_meter_id(session):
    """Valida la inserción de un medidor y su recuperación fiel como entidad de dominio."""
    repo = SqlAlchemyMeterRepository(session)
    meter = Meter(
        id="M-101",
        meter_id="M-101",
        name="Medidor 101",
        location="Planta Norte",
        status="active",
    )

    repo.save(meter)

    retrieved = repo.get_by_meter_id("M-101")
    assert retrieved is not None
    assert isinstance(retrieved, Meter)
    assert retrieved.meter_id == "M-101"
    assert retrieved.name == "Medidor 101"
    assert retrieved.location == "Planta Norte"
    assert retrieved.status == "active"
    assert retrieved.id != ""


def test_get_by_meter_id_not_found(session):
    """Valida que un meter_id inexistente retorne None."""
    repo = SqlAlchemyMeterRepository(session)
    assert repo.get_by_meter_id("NON_EXISTENT") is None


def test_save_idempotence(session):
    """Valida RN-04: guardar dos veces el mismo meter_id no duplica ni falla."""
    repo = SqlAlchemyMeterRepository(session)
    meter1 = Meter(
        id="M-102",
        meter_id="M-102",
        name="Medidor 102 Original",
        location="Planta Sur",
        status="active",
    )
    repo.save(meter1)

    # Intentar guardar de nuevo el mismo meter_id (posiblemente con otro nombre)
    meter2 = Meter(
        id="M-102",
        meter_id="M-102",
        name="Medidor 102 Modificado",
        location="Planta Sur",
        status="active",
    )
    repo.save(meter2)

    all_meters = repo.get_all()
    assert len(all_meters) == 1
    assert all_meters[0].meter_id == "M-102"
    # Debe conservar el original sin duplicar ni modificar
    assert all_meters[0].name == "Medidor 102 Original"
