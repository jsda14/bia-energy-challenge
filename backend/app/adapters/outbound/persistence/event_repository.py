"""Implementación de EventRepositoryPort mediante SQLAlchemy."""

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.adapters.outbound.persistence.db import get_session
from app.adapters.outbound.persistence.orm_models import EventORM
from app.domain.models.event import Event, EventType
from app.domain.ports.event_repository_port import EventRepositoryPort


class SqlAlchemyEventRepository(EventRepositoryPort):
    """Adaptador de persistencia para eventos operativos utilizando SQLAlchemy ORM y SQLite."""

    def __init__(self, session: Session | Engine) -> None:
        """Inicializa el repositorio con una sesión o motor de SQLAlchemy.

        Args:
            session: Instancia de SQLAlchemy Session o Engine.
        """
        if isinstance(session, Engine):
            self._session = get_session(session)
        else:
            self._session = session

    def get_by_meter_id(self, meter_id: str) -> list[Event]:
        """Retorna todos los eventos de un medidor, ordenados por event_timestamp ascendente.

        Si el medidor no tiene eventos, retorna una lista vacía.

        Args:
            meter_id: Código identificador del medidor.

        Returns:
            Lista de entidades de dominio Event ordenadas cronológicamente.
        """
        stmt = (
            select(EventORM)
            .where(EventORM.meter_id == meter_id)
            .order_by(EventORM.event_timestamp.asc())
        )
        rows = self._session.scalars(stmt).all()
        return [
            Event(
                meter_id=row.meter_id,
                event_timestamp=row.event_timestamp,
                event_type=EventType(row.event_type),
                description=row.description,
            )
            for row in rows
        ]

    def get_all(self) -> list[Event]:
        """Retorna todos los eventos registrados de todos los medidores, ordenados cronológicamente.

        Returns:
            Lista de entidades de dominio Event.
        """
        stmt = select(EventORM).order_by(EventORM.event_timestamp.asc())
        rows = self._session.scalars(stmt).all()
        return [
            Event(
                meter_id=row.meter_id,
                event_timestamp=row.event_timestamp,
                event_type=EventType(row.event_type),
                description=row.description,
            )
            for row in rows
        ]

    def save_many(self, events: list[Event]) -> None:
        """Inserta eventos en bloque de forma idempotente por (meter_id, event_timestamp, event_type).

        Si ya existe un evento con esa combinación exacta, no lo duplica ni lanza error (RN-04).

        Args:
            events: Lista de entidades de dominio Event a persistir.
        """
        if not events:
            return

        meter_ids = {e.meter_id for e in events}
        existing_stmt = select(
            EventORM.meter_id, EventORM.event_timestamp, EventORM.event_type
        ).where(EventORM.meter_id.in_(meter_ids))
        existing_triplets = set(self._session.execute(existing_stmt).all())

        seen = set(existing_triplets)
        to_insert: list[EventORM] = []

        for e in events:
            ev_type_str = (
                e.event_type.value
                if isinstance(e.event_type, EventType)
                else str(e.event_type)
            )
            key = (e.meter_id, e.event_timestamp, ev_type_str)
            if key not in seen:
                seen.add(key)
                to_insert.append(
                    EventORM(
                        meter_id=e.meter_id,
                        event_timestamp=e.event_timestamp,
                        event_type=ev_type_str,
                        description=e.description,
                    )
                )

        if to_insert:
            self._session.add_all(to_insert)
            self._session.flush()
