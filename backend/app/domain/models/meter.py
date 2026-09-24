"""Modelo de dominio para medidores eléctricos."""

from pydantic import BaseModel, Field


class Meter(BaseModel):
    """Modelo de dominio inmutable que representa un medidor eléctrico.

    Attributes:
        id: Identificador único interno.
        meter_id: Código del medidor, p.ej. 'M-109'.
        name: Nombre descriptivo del medidor.
        location: Ubicación física o instalación del medidor.
        status: Estado operativo del medidor ('active' o 'inactive').
    """

    model_config = {"frozen": True}

    id: str = Field(..., description="Identificador único interno")
    meter_id: str = Field(..., description="Código del medidor, p.ej. 'M-109'")
    name: str
    location: str
    status: str  # "active" | "inactive"
