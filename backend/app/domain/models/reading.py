"""Modelo de dominio para lecturas horarias de medidores."""

from datetime import datetime
from pydantic import BaseModel, Field


class Reading(BaseModel):
    """Lectura horaria inmutable de consumo y variables eléctricas de un medidor.

    Attributes:
        meter_id: Código del medidor asociado a la lectura.
        timestamp: Fecha y hora exacta de la lectura.
        consumption_kwh: Energía consumida en kilovatios-hora.
        voltage_v: Voltaje medido en voltios.
        current_a: Corriente medida en amperios.
        power_factor: Factor de potencia medido.
        status: Estado reportado por el origen de datos (por defecto 'OK').
    """

    model_config = {"frozen": True}

    meter_id: str
    timestamp: datetime
    consumption_kwh: float
    voltage_v: float
    current_a: float
    power_factor: float
    status: str = Field(default="OK")  # status tal como viene del CSV origen
