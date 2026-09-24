"""Puerto de repositorio para entidades de dominio Reading."""

from datetime import datetime
from typing import Protocol

from app.domain.models.reading import Reading


class ReadingRepositoryPort(Protocol):
    """Puerto que define el contrato de persistencia para lecturas horarias."""

    def get_by_meter_id(self, meter_id: str) -> list[Reading]:
        """Retorna todas las lecturas de un medidor, ordenadas por timestamp
        ascendente. Lista vacía si el medidor no tiene lecturas o no existe.
        """
        ...

    def get_by_meter_id_and_range(
        self, meter_id: str, start: datetime, end: datetime
    ) -> list[Reading]:
        """Retorna las lecturas de un medidor cuyo timestamp está dentro de
        [start, end] (inclusive en ambos extremos), ordenadas ascendente.
        """
        ...

    def save_many(self, readings: list[Reading]) -> None:
        """Inserta lecturas en bloque. Idempotente por (meter_id, timestamp):
        si ya existe una lectura con esa combinación, no la duplica.
        """
        ...
