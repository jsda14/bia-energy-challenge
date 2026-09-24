"""Implementación de MeterRepositoryPort mediante SQLAlchemy."""

from datetime import datetime
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.adapters.outbound.persistence.db import get_session
from app.adapters.outbound.persistence.orm_models import MeterORM
from app.domain.models.meter import Meter
from app.domain.ports.meter_repository_port import MeterRepositoryPort


class SqlAlchemyMeterRepository(MeterRepositoryPort):
    """Adaptador de persistencia para medidores utilizando SQLAlchemy ORM y SQLite."""

    def __init__(self, session: Session | Engine) -> None:
        """Inicializa el repositorio con una sesión o motor de SQLAlchemy.

        Args:
            session: Instancia de SQLAlchemy Session o Engine.
        """
        if isinstance(session, Engine):
            self._session = get_session(session)
        else:
            self._session = session

    def get_all(self) -> list[Meter]:
        """Retorna todos los medidores registrados, ordenados por id.

        Returns:
            Lista de entidades de dominio Meter.
        """
        stmt = select(MeterORM).order_by(MeterORM.id.asc())
        rows = self._session.scalars(stmt).all()
        return [
            Meter(
                id=str(row.id),
                meter_id=row.meter_id,
                name=row.name,
                location=row.location,
                status=row.status,
            )
            for row in rows
        ]

    def get_by_meter_id(self, meter_id: str) -> Meter | None:
        """Retorna el medidor cuyo campo meter_id coincide, o None si no existe.

        Args:
            meter_id: Código identificador del medidor (ej. 'M-109').

        Returns:
            Entidad de dominio Meter encontrada o None.
        """
        stmt = select(MeterORM).where(MeterORM.meter_id == meter_id)
        row = self._session.scalars(stmt).first()
        if row is None:
            return None
        return Meter(
            id=str(row.id),
            meter_id=row.meter_id,
            name=row.name,
            location=row.location,
            status=row.status,
        )

    def save(self, meter: Meter) -> None:
        """Inserta el medidor si no existe (idempotente por meter_id).

        Si ya existe un registro con ese meter_id, no lo duplica ni lo modifica.

        Args:
            meter: Entidad de dominio Meter a persistir.
        """
        stmt = select(MeterORM).where(MeterORM.meter_id == meter.meter_id)
        existing = self._session.scalars(stmt).first()
        if existing is not None:
            return

        new_meter = MeterORM(
            meter_id=meter.meter_id,
            name=meter.name,
            location=meter.location,
            status=meter.status,
            created_at=datetime.utcnow(),
        )
        self._session.add(new_meter)
        self._session.commit()
