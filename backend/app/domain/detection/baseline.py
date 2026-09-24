"""Cálculo determinista de línea base (baseline) de consumo para medidores."""

from datetime import datetime, timedelta
import statistics

from app.domain.models.reading import Reading


def calculate_baseline(
    readings: list[Reading],
    evaluation_window_start: datetime,
    evaluation_window_end: datetime,
    lookback_days: int = 7,
) -> float:
    """Calcula el baseline de consumo (kWh promedio por lectura) para un medidor.

    Usa lecturas de la misma hora del día anteriores a `evaluation_window_start`
    dentro de `lookback_days` días, excluyendo cualquier lectura dentro de la
    ventana de evaluación. Implementa un fallback en cascada si no hay suficientes
    muestras horarias (RN-01).

    Args:
        readings: Histórico de lecturas de un medidor (mismo meter_id), no
            necesariamente ordenado.
        evaluation_window_start: Inicio de la ventana que se está evaluando.
        evaluation_window_end: Fin de la ventana que se está evaluando.
        lookback_days: Días hacia atrás desde evaluation_window_start a considerar.

    Returns:
        Promedio de consumption_kwh de las lecturas seleccionadas según la cascada
        de resolución horaria (RN-01).

    Raises:
        ValueError: Si `readings` está vacío, o si no existe ninguna lectura
            anterior a evaluation_window_start (CB-01 extremo).
    """
    if not readings:
        raise ValueError("The readings list cannot be empty.")

    prior_readings = [r for r in readings if r.timestamp < evaluation_window_start]
    if not prior_readings:
        raise ValueError(
            f"No readings found prior to evaluation_window_start ({evaluation_window_start})."
        )

    target_hour = evaluation_window_start.hour
    min_samples = max(3, lookback_days // 3)

    cutoff = evaluation_window_start - timedelta(days=lookback_days)
    lookback_readings = [r for r in prior_readings if r.timestamp >= cutoff]

    # Fallback 2.a: Lecturas de la misma hora del día dentro del lookback de lookback_days
    same_hour_lookback = [
        r for r in lookback_readings if r.timestamp.hour == target_hour
    ]
    if len(same_hour_lookback) >= min_samples:
        return float(statistics.mean(r.consumption_kwh for r in same_hour_lookback))

    # Fallback 2.b: Todas las lecturas de la misma hora en todo el histórico previo
    same_hour_all = [
        r for r in prior_readings if r.timestamp.hour == target_hour
    ]
    if len(same_hour_all) >= min_samples:
        return float(statistics.mean(r.consumption_kwh for r in same_hour_all))

    # Fallback 2.c: Comportamiento plano previo (en lookback o histórico previo total)
    selected_readings = lookback_readings if lookback_readings else prior_readings
    return float(statistics.mean(r.consumption_kwh for r in selected_readings))
