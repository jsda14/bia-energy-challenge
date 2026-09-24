"""Modelos de dominio para representación y evidencia de anomalías."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class AnomalyType(str, Enum):
    """Clasificación determinista del tipo de anomalía detectada.

    Attributes:
        REAL_ANOMALY: Anomalía real sin justificación operativa conocida.
        EXPLAINABLE_ANOMALY: Anomalía explicada por un cambio operacional conocido.
        FALSE_POSITIVE: Desviación esperada por un corte o mantenimiento programado.
        DATA_QUALITY: Inconsistencia en variables eléctricas o datos de medición.
    """

    REAL_ANOMALY = "REAL_ANOMALY"
    EXPLAINABLE_ANOMALY = "EXPLAINABLE_ANOMALY"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    DATA_QUALITY = "DATA_QUALITY"


class Severity(str, Enum):
    """Nivel de severidad de la anomalía según impacto y magnitudes detectadas.

    Attributes:
        LOW: Severidad baja (p.ej. falsos positivos o variaciones menores).
        MEDIUM: Severidad media (p.ej. variaciones entre 30% y 80%).
        HIGH: Severidad alta (p.ej. variaciones >= 80% o fallas eléctricas críticas).
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AnomalyEvidence(BaseModel):
    """Evidencia cuantitativa y contexto temporal de una anomalía detectada.

    Attributes:
        baseline_kwh: Consumo de referencia en kWh calculado previo a la ventana.
        observed_kwh: Consumo promedio observado en kWh durante la ventana.
        variation_pct: Variación porcentual observada respecto al baseline.
        affected_variables: Subconjunto de variables con anomalía.
        correlated_event: Descripción del evento correlacionado si existe.
        window_start: Inicio del rango temporal de la anomalía.
        window_end: Fin del rango temporal de la anomalía.
    """

    model_config = {"frozen": True}

    baseline_kwh: float
    observed_kwh: float
    variation_pct: float
    affected_variables: list[str]  # subset of: consumption_kwh, voltage_v, current_a, power_factor
    correlated_event: str | None = None  # description del Event correlacionado, si existe
    window_start: datetime
    window_end: datetime


class AnomalyRecord(BaseModel):
    """Registro inmutable de una anomalía detectada y clasificada por el dominio.

    Attributes:
        meter_id: Código del medidor analizado.
        detected_at: Marca temporal de ejecución del análisis.
        type: Clasificación final del tipo de anomalía.
        severity: Nivel de severidad asignado.
        confidence: Nivel de confianza determinista en rango [0.0, 1.0].
        evidence: Detalle de evidencia numérica y temporal.
    """

    model_config = {"frozen": True}

    meter_id: str
    detected_at: datetime
    type: AnomalyType
    severity: Severity
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: AnomalyEvidence
