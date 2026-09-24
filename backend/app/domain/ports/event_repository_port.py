"""Puerto de repositorio para entidades de dominio Event."""

from typing import Protocol

from app.domain.models.event import Event


class EventRepositoryPort(Protocol):
    """Puerto que define el contrato de persistencia para eventos operativos conocidos."""

    def get_by_meter_id(self, meter_id: str) -> list[Event]:
        """Retorna todos los eventos de un medidor, ordenados por
        event_timestamp ascendente. Lista vacía si no hay eventos.
        """
        ...

    def get_all(self) -> list[Event]:
        """Retorna todos los eventos registrados, de todos los medidores."""
        ...

    def save_many(self, events: list[Event]) -> None:
        """Inserta eventos en bloque. Idempotente por (meter_id,
        event_timestamp, event_type): si ya existe un evento con esa
        combinación exacta, no lo duplica.
        """
        ...
