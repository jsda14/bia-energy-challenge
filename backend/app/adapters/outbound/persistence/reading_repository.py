"""Implementación de ReadingRepositoryPort mediante SQLAlchemy."""

from datetime import datetime
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.adapters.outbound.persistence.db import get_session
from app.adapters.outbound.persistence.orm_models import ReadingORM
from app.domain.models.reading import Reading
from app.domain.ports.reading_repository_port import ReadingRepositoryPort


class SqlAlchemyReadingRepository(ReadingRepositoryPort):
    """Adaptador de persistencia para lecturas horarias utilizando SQLAlchemy ORM y SQLite."""

    def __init__(self, session: Session | Engine) -> None:
        """Inicializa el repositorio con una sesión o motor de SQLAlchemy.

        Args:
            session: Instancia de SQLAlchemy Session o Engine.
        """
        if isinstance(session, Engine):
            self._session = get_session(session)
        else:
            self._session = session

    def get_by_meter_id(self, meter_id: str) -> list[Reading]:
        """Retorna todas las lecturas de un medidor, ordenadas por timestamp ascendente.

        Si el medidor no tiene lecturas o no existe, retorna una lista vacía (CB-02).

        Args:
            meter_id: Código identificador del medidor.

        Returns:
            Lista de entidades de dominio Reading ordenadas cronológicamente.
        """
        stmt = (
            select(ReadingORM)
            .where(ReadingORM.meter_id == meter_id)
            .order_by(ReadingORM.timestamp.asc())
        )
        rows = self._session.scalars(stmt).all()
        return [
            Reading(
                meter_id=row.meter_id,
                timestamp=row.timestamp,
                consumption_kwh=row.consumption_kwh,
                voltage_v=row.voltage_v,
                current_a=row.current_a,
                power_factor=row.power_factor,
                status=row.status,
            )
            for row in rows
        ]

    def get_by_meter_id_and_range(
        self, meter_id: str, start: datetime, end: datetime
    ) -> list[Reading]:
        """Retorna las lecturas de un medidor cuyo timestamp está dentro de [start, end].

        Si el rango no intersecta ninguna lectura, retorna una lista vacía (CB-03).

        Args:
            meter_id: Código identificador del medidor.
            start: Fecha/hora de inicio (inclusive).
            end: Fecha/hora de fin (inclusive).

        Returns:
            Lista de entidades de dominio Reading dentro del rango, ordenadas cronológicamente.
        """
        stmt = (
            select(ReadingORM)
            .where(
                ReadingORM.meter_id == meter_id,
                ReadingORM.timestamp >= start,
                ReadingORM.timestamp <= end,
            )
            .order_by(ReadingORM.timestamp.asc())
        )
        rows = self._session.scalars(stmt).all()
        return [
            Reading(
                meter_id=row.meter_id,
                timestamp=row.timestamp,
                consumption_kwh=row.consumption_kwh,
                voltage_v=row.voltage_v,
                current_a=row.current_a,
                power_factor=row.power_factor,
                status=row.status,
            )
            for row in rows
        ]

    def save_many(self, readings: list[Reading]) -> None:
        """Inserta lecturas en bloque de forma idempotente por (meter_id, timestamp).

        Si ya existe una lectura con esa combinación, no la duplica ni genera error (RN-04).

        Args:
            readings: Lista de entidades de dominio Reading a persistir.
        """
        if not readings:
            return

        meter_ids = {r.meter_id for r in readings}
        existing_stmt = select(ReadingORM.meter_id, ReadingORM.timestamp).where(
            ReadingORM.meter_id.in_(meter_ids)
        )
        existing_pairs = set(self._session.execute(existing_stmt).all())

        seen = set(existing_pairs)
        to_insert: list[ReadingORM] = []

        for r in readings:
            key = (r.meter_id, r.timestamp)
            if key not in seen:
                seen.add(key)
                to_insert.append(
                    ReadingORM(
                        meter_id=r.meter_id,
                        timestamp=r.timestamp,
                        consumption_kwh=r.consumption_kwh,
                        voltage_v=r.voltage_v,
                        current_a=r.current_a,
                        power_factor=r.power_factor,
                        status=r.status,
                    )
                )

        if to_insert:
            self._session.add_all(to_insert)
            self._session.flush()
