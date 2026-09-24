"""Puerto de repositorio para entidades de dominio Meter."""

from typing import Protocol

from app.domain.models.meter import Meter


class MeterRepositoryPort(Protocol):
    """Puerto que define el contrato de persistencia para medidores eléctricos."""

    def get_all(self) -> list[Meter]:
        """Retorna todos los medidores registrados, sin filtros."""
        ...

    def get_by_meter_id(self, meter_id: str) -> Meter | None:
        """Retorna el medidor cuyo campo meter_id coincide, o None si no existe."""
        ...

    def save(self, meter: Meter) -> None:
        """Inserta el medidor si no existe (idempotente por meter_id); si ya
        existe un registro con ese meter_id, no lo duplica ni lo modifica.
        """
        ...
