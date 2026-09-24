"""Modelo de dominio para eventos operativos conocidos."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class EventType(str, Enum):
    """Tipos de eventos operativos conocidos que afectan el comportamiento de un medidor.

    Attributes:
        OPERATIONAL_CHANGE: Cambio operacional planeado (p.ej. nueva línea de producción).
        SCHEDULED_OUTAGE: Corte de energía o mantenimiento programado.
        DATA_QUALITY: Evento asociado a problemas de sensores o calidad de datos.
        UNKNOWN: Evento de causa no determinada o no operativa.
    """

    OPERATIONAL_CHANGE = "OPERATIONAL_CHANGE"
    SCHEDULED_OUTAGE = "SCHEDULED_OUTAGE"
    DATA_QUALITY = "DATA_QUALITY"
    UNKNOWN = "UNKNOWN"


class Event(BaseModel):
    """Evento operativo inmutable asociado al historial de un medidor.

    Attributes:
        meter_id: Código del medidor al que aplica el evento.
        event_timestamp: Fecha y hora en la que ocurrió o inició el evento.
        event_type: Tipo de evento según la clasificación EventType.
        description: Detalle textual del evento.
    """

    model_config = {"frozen": True}

    meter_id: str
    event_timestamp: datetime
    event_type: EventType
    description: str
