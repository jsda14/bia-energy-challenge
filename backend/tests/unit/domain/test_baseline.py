"""Tests unitarios para la función calculate_baseline (RN-01, CB-01, CB-02)."""

from datetime import datetime, timedelta
import pytest

from app.domain.detection.baseline import calculate_baseline
from app.domain.models.reading import Reading


def _create_reading(
    meter_id: str,
    timestamp: datetime,
    consumption: float,
    voltage: float = 220.0,
    current: float = 15.0,
    pf: float = 0.95,
) -> Reading:
    """Helper para crear instancias de Reading en tests."""
    return Reading(
        meter_id=meter_id,
        timestamp=timestamp,
        consumption_kwh=consumption,
        voltage_v=voltage,
        current_a=current,
        power_factor=pf,
    )


def test_calculate_baseline_standard_lookback():
    """Valida RN-01: cálculo del promedio de lecturas en los N días previos."""
    base_time = datetime(2026, 9, 10, 0, 0)
    readings = []

    # 10 días previos de datos: días 0 a 2 tienen 20 kWh, días 3 a 9 (7 días) tienen 50 kWh
    for day in range(10):
        val = 20.0 if day < 3 else 50.0
        for hour in range(24):
            ts = base_time - timedelta(days=10 - day) + timedelta(hours=hour)
            readings.append(_create_reading("M-101", ts, val))

    eval_start = base_time
    eval_end = base_time + timedelta(hours=12)

    # Con lookback_days=7, debe promediar solo los últimos 7 días previos (consumo 50.0)
    baseline = calculate_baseline(
        readings, eval_start, eval_end, lookback_days=7
    )
    assert baseline == pytest.approx(50.0)


def test_calculate_baseline_excludes_evaluation_window():
    """Valida RN-01: las lecturas dentro de la ventana de evaluación NO afectan el baseline."""
    base_time = datetime(2026, 9, 10, 0, 0)
    readings = []

    # 3 días previos con consumo 30.0
    for day in range(3):
        for hour in range(24):
            ts = base_time - timedelta(days=3 - day) + timedelta(hours=hour)
            readings.append(_create_reading("M-101", ts, 30.0))

    eval_start = base_time
    eval_end = base_time + timedelta(hours=24)

    # Durante la ventana de evaluación el consumo se dispara a 200.0
    for hour in range(24):
        ts = eval_start + timedelta(hours=hour)
        readings.append(_create_reading("M-101", ts, 200.0))

    baseline = calculate_baseline(readings, eval_start, eval_end, lookback_days=7)
    # Debe ser exactamente 30.0, sin ser contaminado por el 200.0 de la ventana
    assert baseline == pytest.approx(30.0)


def test_calculate_baseline_insufficient_history_fallback():
    """Valida CB-01: si hay menos de lookback_days de historial, usa todo lo disponible."""
    base_time = datetime(2026, 9, 5, 12, 0)
    readings = []

    # Solo 2 días de historial previo disponibles (promedio 45.0)
    for day in range(2):
        for hour in range(24):
            ts = base_time - timedelta(days=2 - day) + timedelta(hours=hour)
            readings.append(_create_reading("M-101", ts, 45.0))

    eval_start = base_time
    eval_end = base_time + timedelta(hours=6)

    # Se solicita lookback_days=7 pero solo existen 2 días
    baseline = calculate_baseline(readings, eval_start, eval_end, lookback_days=7)
    assert baseline == pytest.approx(45.0)


def test_calculate_baseline_empty_readings_raises_value_error():
    """Valida CB-01: lista vacía de lecturas genera ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        calculate_baseline([], datetime(2026, 9, 1, 0, 0), datetime(2026, 9, 1, 6, 0))


def test_calculate_baseline_no_prior_readings_raises_value_error():
    """Valida CB-01 extremo: cuando no existe ninguna lectura anterior a la ventana."""
    eval_start = datetime(2026, 9, 1, 10, 0)
    readings = [
        _create_reading("M-101", eval_start + timedelta(hours=1), 50.0),
        _create_reading("M-101", eval_start + timedelta(hours=2), 60.0),
    ]
    with pytest.raises(ValueError, match="No readings found prior"):
        calculate_baseline(readings, eval_start, eval_start + timedelta(hours=4))


def test_calculate_baseline_unordered_readings_and_gaps():
    """Valida CB-02: lecturas desordenadas y con saltos temporales se procesan correctamente."""
    base_time = datetime(2026, 9, 10, 0, 0)
    # Lista desordenada con gaps
    readings = [
        _create_reading("M-101", base_time - timedelta(hours=10), 40.0),
        _create_reading("M-101", base_time - timedelta(hours=2), 60.0),
        _create_reading("M-101", base_time - timedelta(hours=20), 50.0),
    ]

    eval_start = base_time
    eval_end = base_time + timedelta(hours=5)

    baseline = calculate_baseline(readings, eval_start, eval_end, lookback_days=1)
    # (40 + 60 + 50) / 3 = 50.0
    assert baseline == pytest.approx(50.0)


def test_calculate_baseline_hourly_matching():
    """Valida PARTE 1: evalua solo lecturas de la misma hora del día en el lookback."""
    base_time = datetime(2026, 9, 10, 14, 0)
    readings = []

    # 7 días previos con patrón diurno: 20 kWh a las 02:00 y 80 kWh a las 14:00
    for day in range(7):
        ts_night = base_time - timedelta(days=7 - day, hours=12)  # 02:00
        ts_day = base_time - timedelta(days=7 - day)  # 14:00
        readings.append(_create_reading("M-101", ts_night, 20.0))
        readings.append(_create_reading("M-101", ts_day, 80.0))

    # A las 14:00 debe promediar solo las lecturas de las 14:00 (80.0 kWh)
    baseline_day = calculate_baseline(readings, base_time, base_time, lookback_days=7)
    assert baseline_day == pytest.approx(80.0)

    # A las 02:00 debe promediar solo las lecturas de las 02:00 (20.0 kWh)
    eval_night = base_time - timedelta(hours=12)
    baseline_night = calculate_baseline(readings, eval_night, eval_night, lookback_days=7)
    assert baseline_night == pytest.approx(20.0)


def test_calculate_baseline_fallback_all_history_same_hour():
    """Valida Fallback 2.b: si el lookback no alcanza min_samples, expande a todo el histórico."""
    base_time = datetime(2026, 9, 10, 10, 0)
    readings = []

    # 5 días en total, pero lookback_days=2 (solo 2 días dentro del lookback, min_samples=max(3, 2//3)=3)
    # Lecturas de las 10:00 con 60.0 kWh
    for day in range(5):
        ts = base_time - timedelta(days=5 - day)
        readings.append(_create_reading("M-101", ts, 60.0))

    # Con lookback_days=2, hay 2 lecturas en lookback (< 3), pero 5 en histórico total (>= 3)
    baseline = calculate_baseline(readings, base_time, base_time, lookback_days=2)
    assert baseline == pytest.approx(60.0)

