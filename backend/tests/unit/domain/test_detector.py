"""Tests unitarios para AnomalyDetector cubriendo RN-01..RN-07 y CB-01..CB-06."""

from datetime import datetime, timedelta
import pytest

from app.domain.detection.detector import AnomalyDetector
from app.domain.models.anomaly import AnomalyType, Severity
from app.domain.models.event import Event, EventType
from app.domain.models.reading import Reading


def _make_reading(
    meter_id: str,
    timestamp: datetime,
    consumption: float,
    voltage: float = 220.0,
    current: float = 20.0,
    pf: float = 0.95,
) -> Reading:
    """Helper para construir un objeto Reading en tests."""
    return Reading(
        meter_id=meter_id,
        timestamp=timestamp,
        consumption_kwh=consumption,
        voltage_v=voltage,
        current_a=current,
        power_factor=pf,
    )


def test_m109_real_anomaly_pattern():
    """Valida patrón M-109: ~2x baseline, caída de voltaje, corriente alta, PF colapsado, sin evento operativo."""
    start_date = datetime(2026, 9, 1, 0, 0)
    readings: list[Reading] = []

    # 10 días de lecturas normales (consumo ~50 kWh, 220V, 20A, PF 0.95)
    for hour in range(240):
        ts = start_date + timedelta(hours=hour)
        readings.append(_make_reading("M-109", ts, 50.0, 220.0, 20.0, 0.95))

    # A partir de la hora 240, step-change a ~100 kWh (~100% variación), V=190V, I=42A, PF=0.75 durante 24h
    anomaly_start = start_date + timedelta(hours=240)
    for hour in range(24):
        ts = anomaly_start + timedelta(hours=hour)
        readings.append(_make_reading("M-109", ts, 100.0, 190.0, 42.0, 0.75))

    # Evento UNKNOWN no debe reclasificar (RN-05)
    unknown_event = Event(
        meter_id="M-109",
        event_timestamp=anomaly_start,
        event_type=EventType.UNKNOWN,
        description="Evento no operativo no identificado",
    )

    detector = AnomalyDetector()
    results = detector.analyze(
        "M-109", readings, [unknown_event], analysis_timestamp=datetime(2026, 9, 15, 0, 0)
    )

    assert len(results) == 1
    record = results[0]
    assert record.meter_id == "M-109"
    assert record.type == AnomalyType.REAL_ANOMALY
    assert record.severity == Severity.HIGH
    assert 0.0 <= record.confidence <= 1.0
    assert record.confidence >= 0.8
    assert "consumption_kwh" in record.evidence.affected_variables
    assert "voltage_v" in record.evidence.affected_variables
    assert "current_a" in record.evidence.affected_variables
    assert "power_factor" in record.evidence.affected_variables
    assert record.evidence.correlated_event == "Evento no operativo no identificado"


def test_m104_explainable_anomaly_pattern():
    """Valida patrón M-104: step-change sostenido (+45%) con evento OPERATIONAL_CHANGE."""
    start_date = datetime(2026, 9, 1, 0, 0)
    readings: list[Reading] = []

    # 10 días normales (consumo 50 kWh)
    for hour in range(240):
        ts = start_date + timedelta(hours=hour)
        readings.append(_make_reading("M-104", ts, 50.0))

    # Step change de 45% (72.5 kWh) durante 24h
    change_start = start_date + timedelta(hours=240)
    for hour in range(24):
        ts = change_start + timedelta(hours=hour)
        readings.append(_make_reading("M-104", ts, 72.5, 220.0, 29.0, 0.95))

    event = Event(
        meter_id="M-104",
        event_timestamp=change_start - timedelta(hours=2),
        event_type=EventType.OPERATIONAL_CHANGE,
        description="Puesta en marcha de nueva línea productiva",
    )

    detector = AnomalyDetector()
    results = detector.analyze(
        "M-104", readings, [event], analysis_timestamp=datetime(2026, 9, 15, 0, 0)
    )

    assert len(results) == 1
    record = results[0]
    assert record.type == AnomalyType.EXPLAINABLE_ANOMALY
    assert record.severity == Severity.MEDIUM
    assert 0.0 <= record.confidence <= 1.0
    assert record.evidence.correlated_event == "Puesta en marcha de nueva línea productiva"


def test_m106_false_positive_pattern():
    """Valida patrón M-106: caída a near-zero con evento SCHEDULED_OUTAGE."""
    start_date = datetime(2026, 9, 1, 0, 0)
    readings: list[Reading] = []

    # 7 días normales (consumo 60 kWh)
    for hour in range(168):
        ts = start_date + timedelta(hours=hour)
        readings.append(_make_reading("M-106", ts, 60.0))

    # Caída a 10 kWh (-83%) durante 11 horas
    outage_start = start_date + timedelta(hours=168)
    for hour in range(11):
        ts = outage_start + timedelta(hours=hour)
        readings.append(_make_reading("M-106", ts, 10.0, 220.0, 3.0, 0.95))

    event = Event(
        meter_id="M-106",
        event_timestamp=outage_start,
        event_type=EventType.SCHEDULED_OUTAGE,
        description="Mantenimiento preventivo programado subestación",
    )

    detector = AnomalyDetector()
    results = detector.analyze(
        "M-106", readings, [event], analysis_timestamp=datetime(2026, 9, 15, 0, 0)
    )

    assert len(results) == 1
    record = results[0]
    assert record.type == AnomalyType.FALSE_POSITIVE
    assert record.severity == Severity.LOW  # RN-06: LOW para FALSE_POSITIVE siempre
    assert 0.0 <= record.confidence <= 1.0


def test_m112_data_quality_pattern():
    """Valida patrón M-112: consumo normal, voltaje y factor de potencia erráticos con evento DATA_QUALITY."""
    start_date = datetime(2026, 9, 1, 0, 0)
    readings: list[Reading] = []

    # 10 días normales
    for hour in range(240):
        ts = start_date + timedelta(hours=hour)
        readings.append(_make_reading("M-112", ts, 50.0, 220.0, 20.0, 0.95))

    # Consumo sigue normal (50 kWh), pero voltaje y PF alternan erráticamente
    anomaly_start = start_date + timedelta(hours=240)
    for hour in range(24):
        ts = anomaly_start + timedelta(hours=hour)
        if hour % 2 == 0:
            readings.append(_make_reading("M-112", ts, 50.0, 185.0, 20.0, 0.60))
        else:
            readings.append(_make_reading("M-112", ts, 50.0, 255.0, 20.0, 0.95))

    event = Event(
        meter_id="M-112",
        event_timestamp=anomaly_start,
        event_type=EventType.DATA_QUALITY,
        description="Falla de calibración en transformador de potencial",
    )

    detector = AnomalyDetector()
    results = detector.analyze(
        "M-112", readings, [event], analysis_timestamp=datetime(2026, 9, 15, 0, 0)
    )

    assert len(results) == 1
    record = results[0]
    assert record.type == AnomalyType.DATA_QUALITY
    assert record.severity == Severity.HIGH  # RN-06: > 20% lecturas fuera de rango
    assert "consumption_kwh" not in record.evidence.affected_variables
    assert "voltage_v" in record.evidence.affected_variables
    assert "power_factor" in record.evidence.affected_variables


def test_normal_meter_returns_empty_list():
    """Valida CB-03: medidor sin anomalías retorna lista vacía limpiamente."""
    start_date = datetime(2026, 9, 1, 0, 0)
    readings: list[Reading] = []

    for hour in range(168):
        ts = start_date + timedelta(hours=hour)
        readings.append(_make_reading("M-101", ts, 50.0, 220.0, 20.0, 0.95))

    detector = AnomalyDetector()
    results = detector.analyze(
        "M-101", readings, [], analysis_timestamp=datetime(2026, 9, 10, 0, 0)
    )
    assert results == []


def test_isolated_outlier_zscore():
    """Valida RN-03: outlier puntual aislado con z-score >= 3.0."""
    start_date = datetime(2026, 9, 1, 0, 0)
    readings: list[Reading] = []

    # 100 horas normales con consumo 50.0
    for hour in range(100):
        ts = start_date + timedelta(hours=hour)
        readings.append(_make_reading("M-105", ts, 50.0))

    # 1 hora con spike extremo (200.0 kWh), luego vuelve a 50.0
    spike_ts = start_date + timedelta(hours=100)
    readings.append(_make_reading("M-105", spike_ts, 200.0))

    for hour in range(101, 150):
        ts = start_date + timedelta(hours=hour)
        readings.append(_make_reading("M-105", ts, 50.0))

    detector = AnomalyDetector(zscore_threshold=3.0)
    results = detector.analyze(
        "M-105", readings, [], analysis_timestamp=datetime(2026, 9, 10, 0, 0)
    )

    assert len(results) >= 1
    # Encuentra el outlier en spike_ts
    outlier = next(r for r in results if r.evidence.window_start == spike_ts)
    assert outlier.type == AnomalyType.REAL_ANOMALY
    assert outlier.evidence.window_start == outlier.evidence.window_end


def test_inconsistent_meter_id_raises_value_error():
    """Valida CB-04: lectura con meter_id discrepante lanza ValueError de inmediato."""
    readings = [
        _make_reading("M-101", datetime(2026, 9, 1, 0, 0), 50.0),
        _make_reading("M-999", datetime(2026, 9, 1, 1, 0), 50.0),
    ]
    detector = AnomalyDetector()
    with pytest.raises(ValueError, match="does not match target meter_id"):
        detector.analyze("M-101", readings, [], analysis_timestamp=datetime(2026, 9, 2, 0, 0))


def test_empty_readings_raises_value_error():
    """Valida CB-04: lista vacía de lecturas lanza ValueError."""
    detector = AnomalyDetector()
    with pytest.raises(ValueError, match="cannot be empty"):
        detector.analyze("M-101", [], [], analysis_timestamp=datetime(2026, 9, 2, 0, 0))


def test_unrelated_event_does_not_affect_detection():
    """Valida CB-05: evento fuera de rango temporal o de otro medidor no afecta."""
    start_date = datetime(2026, 9, 1, 0, 0)
    readings: list[Reading] = []

    for hour in range(100):
        readings.append(_make_reading("M-101", start_date + timedelta(hours=hour), 50.0))

    # Anomalía sostenida de 5 horas
    for hour in range(100, 106):
        readings.append(_make_reading("M-101", start_date + timedelta(hours=hour), 90.0))

    # Evento para otro medidor o en fecha no relacionada
    distant_event = Event(
        meter_id="M-101",
        event_timestamp=start_date + timedelta(days=20),
        event_type=EventType.OPERATIONAL_CHANGE,
        description="Evento lejano",
    )
    other_meter_event = Event(
        meter_id="M-102",
        event_timestamp=start_date + timedelta(hours=100),
        event_type=EventType.OPERATIONAL_CHANGE,
        description="Evento de otro medidor",
    )

    detector = AnomalyDetector()
    results = detector.analyze(
        "M-101", readings, [distant_event, other_meter_event], analysis_timestamp=datetime(2026, 9, 15, 0, 0)
    )

    assert len(results) == 1
    assert results[0].type == AnomalyType.REAL_ANOMALY
    assert results[0].evidence.correlated_event is None


def test_multiple_anomalies_same_meter():
    """Valida CB-06: medidor con múltiples anomalías no contiguas genera registros independientes."""
    start_date = datetime(2026, 9, 1, 0, 0)
    readings: list[Reading] = []

    # 5 días normales
    for hour in range(120):
        readings.append(_make_reading("M-101", start_date + timedelta(hours=hour), 50.0))

    # Anomalía 1: horas 120-125 (consumo 90 kWh)
    for hour in range(120, 126):
        readings.append(_make_reading("M-101", start_date + timedelta(hours=hour), 90.0))

    # Período de vuelta a la normalidad: horas 126-170
    for hour in range(126, 171):
        readings.append(_make_reading("M-101", start_date + timedelta(hours=hour), 50.0))

    # Anomalía 2: horas 171-180 (consumo 95 kWh)
    for hour in range(171, 181):
        readings.append(_make_reading("M-101", start_date + timedelta(hours=hour), 95.0))

    detector = AnomalyDetector()
    results = detector.analyze(
        "M-101", readings, [], analysis_timestamp=datetime(2026, 9, 15, 0, 0)
    )

    assert len(results) == 2
    assert results[0].evidence.window_start < results[1].evidence.window_start


def test_detector_tolerates_out_of_order_readings():
    """Valida CB-02: el detector ordena internamente lecturas desordenadas."""
    start_date = datetime(2026, 9, 1, 0, 0)
    readings: list[Reading] = []

    for hour in range(80):
        readings.append(_make_reading("M-101", start_date + timedelta(hours=hour), 50.0))

    for hour in range(80, 86):
        readings.append(_make_reading("M-101", start_date + timedelta(hours=hour), 95.0))

    # Desordenar deliberadamente
    reversed_readings = list(reversed(readings))

    detector = AnomalyDetector()
    results = detector.analyze(
        "M-101", reversed_readings, [], analysis_timestamp=datetime(2026, 9, 10, 0, 0)
    )

    assert len(results) == 1
    assert results[0].type == AnomalyType.REAL_ANOMALY


def test_confidence_determinism_and_bounds():
    """Valida RN-07: la confianza es determinista, acotada en [0.0, 1.0] y sensible a duración y eventos."""
    start_date = datetime(2026, 9, 1, 0, 0)
    readings: list[Reading] = []

    for hour in range(100):
        readings.append(_make_reading("M-101", start_date + timedelta(hours=hour), 50.0))

    # Anomalía sostenida de 24 horas (+50%)
    for hour in range(100, 124):
        readings.append(_make_reading("M-101", start_date + timedelta(hours=hour), 75.0))

    detector = AnomalyDetector()

    # Análisis 1 sin evento
    res_no_event = detector.analyze(
        "M-101", readings, [], analysis_timestamp=datetime(2026, 9, 10, 0, 0)
    )
    # Análisis 2 con evento coincidente
    event = Event(
        meter_id="M-101",
        event_timestamp=start_date + timedelta(hours=100),
        event_type=EventType.OPERATIONAL_CHANGE,
        description="Operación programada",
    )
    res_with_event = detector.analyze(
        "M-101", readings, [event], analysis_timestamp=datetime(2026, 9, 10, 0, 0)
    )

    conf_no_event = res_no_event[0].confidence
    conf_with_event = res_with_event[0].confidence

    assert 0.0 <= conf_no_event <= 1.0
    assert 0.0 <= conf_with_event <= 1.0
    assert conf_with_event >= conf_no_event


def test_models_immutability():
    """Valida que los modelos de dominio son inmutables (frozen=True)."""
    from pydantic import ValidationError
    from app.domain.models.meter import Meter

    meter = Meter(
        id="internal-1",
        meter_id="M-109",
        name="Medidor Principal",
        location="Edificio A",
        status="active",
    )
    with pytest.raises(ValidationError):
        meter.status = "inactive"  # type: ignore

    reading = _make_reading("M-109", datetime(2026, 9, 1, 0, 0), 50.0)
    with pytest.raises(ValidationError):
        reading.consumption_kwh = 100.0  # type: ignore


def test_ai_explainer_port_protocol_and_models():
    """Valida el contrato de AIExplainerPort y el modelo AIExplanation."""
    from app.domain.ports.ai_explainer_port import AIExplainerPort, AIExplanation

    explanation = AIExplanation(
        reason="Consumo elevado por fuga o anomalía en transformador",
        recommended_action="Enviar técnico para inspección inmediata",
    )
    assert explanation.reason.startswith("Consumo")
    assert explanation.recommended_action.startswith("Enviar")

    class DummyExplainer:
        def explain(self, anomaly):
            return explanation

    # Debe ser compatible con el protocolo
    base_start = datetime(2026, 9, 1, 0, 0)
    dummy_readings = [
        _make_reading("M-101", base_start + timedelta(hours=h), 50.0)
        for h in range(80)
    ] + [
        _make_reading("M-101", base_start + timedelta(hours=80 + h), 100.0)
        for h in range(10)
    ]
    dummy_anomaly = AnomalyDetector().analyze(
        "M-101",
        dummy_readings,
        [],
        datetime(2026, 9, 6, 0, 0),
    )[0]
    explainer: AIExplainerPort = DummyExplainer()
    out = explainer.explain(dummy_anomaly)
    assert out.reason == explanation.reason


def test_domain_error_hierarchy():
    """Valida que DomainError es subclase de Exception."""
    from app.domain.errors import DomainError

    err = DomainError("Error de dominio")
    assert isinstance(err, Exception)


def test_m112_real_pattern_power_factor_collapse_unfragmented():
    """Valida patrón real M-112: colapso de PF a 0.58-0.72 en >20% de lecturas con voltaje en rango.

    Asegura severidad HIGH (RN-06) y que la ventana no se fragmente en múltiples AnomalyRecord.
    """
    start_date = datetime(2026, 9, 1, 0, 0)
    readings: list[Reading] = []

    # 10 días normales (consumo ~25 kWh, V=220V dentro de rango [200, 245], PF=0.95)
    for hour in range(240):
        ts = start_date + timedelta(hours=hour)
        readings.append(_make_reading("M-112", ts, 25.0, 220.0, 15.0, 0.95))

    # Ventana de 24 horas con voltaje en rango (215V-239V), pero PF colapsando a 0.58-0.72 en 8/24 lecturas (33% > 20%)
    # y una lectura con variación puntual de consumo para verificar que no fragmente la ventana
    anomaly_start = start_date + timedelta(hours=240)
    for hour in range(24):
        ts = anomaly_start + timedelta(hours=hour)
        # Voltaje siempre dentro del rango físico esperado [200.0, 245.0]
        voltage = 215.0 if hour % 2 == 0 else 239.0
        # Power factor colapsa a 0.58-0.72 en horas alternas (8 de 24 horas, > 20%)
        if hour % 3 == 0:
            pf = 0.58 if hour % 2 == 0 else 0.72
        else:
            pf = 0.95
        # Una lectura con consumo elevado para verificar no fragmentación por outlier de consumo
        consumption = 35.0 if hour == 5 else 25.0
        readings.append(_make_reading("M-112", ts, consumption, voltage, 15.0, pf))

    event = Event(
        meter_id="M-112",
        event_timestamp=anomaly_start,
        event_type=EventType.DATA_QUALITY,
        description="Intermittent readings and abnormal electrical jumps",
    )

    detector = AnomalyDetector()
    results = detector.analyze(
        "M-112", readings, [event], analysis_timestamp=datetime(2026, 9, 15, 0, 0)
    )

    # Debe ser exactamente 1 ventana, sin fragmentarse en múltiples AnomalyRecord
    assert len(results) == 1
    record = results[0]
    assert record.type == AnomalyType.DATA_QUALITY
    # Severidad debe ser HIGH según RN-06 por inconsistencia eléctrica fuerte (PF < 0.85 en > 20% de lecturas)
    assert record.severity == Severity.HIGH
    assert "power_factor" in record.evidence.affected_variables
    assert record.evidence.correlated_event == "Intermittent readings and abnormal electrical jumps"


def test_m109_real_pattern_simultaneous_signals_unfragmented():
    """Valida patrón real M-109: consumo +100% y colapso de PF 0.93->0.72 sostenido sin alternancia errática.

    Asegura una sola ventana fusionada (len(results) == 1), type REAL_ANOMALY y severity HIGH.
    """
    start_date = datetime(2026, 9, 1, 0, 0)
    readings: list[Reading] = []

    # 10 días normales (consumo 50.0 kWh, V=220.0, I=20.0, PF=0.93)
    for hour in range(240):
        ts = start_date + timedelta(hours=hour)
        readings.append(_make_reading("M-109", ts, 50.0, 220.0, 20.0, 0.93))

    # Ventana sostenida de 48 horas con consumo +100% (100 kWh), I=42A, V=218V, y PF=0.72 colapsado de forma consistente
    # (sin alternancia errática bueno/malo, transitions == 0)
    anomaly_start = start_date + timedelta(hours=240)
    for hour in range(48):
        ts = anomaly_start + timedelta(hours=hour)
        readings.append(_make_reading("M-109", ts, 100.0, 218.0, 42.0, 0.72))

    unknown_event = Event(
        meter_id="M-109",
        event_timestamp=anomaly_start,
        event_type=EventType.UNKNOWN,
        description="No operational event reported",
    )

    detector = AnomalyDetector()
    results = detector.analyze(
        "M-109", readings, [unknown_event], analysis_timestamp=datetime(2026, 9, 15, 0, 0)
    )

    assert len(results) == 1
    record = results[0]
    assert record.type == AnomalyType.REAL_ANOMALY
    assert record.severity == Severity.HIGH
    assert "consumption_kwh" in record.evidence.affected_variables
    assert "power_factor" in record.evidence.affected_variables
    assert record.evidence.correlated_event == "No operational event reported"


def test_normal_meter_diurnal_pattern_no_anomalies():
    """Valida CB-03: un medidor 100% normal con ciclo diurno realista no reporta falsas anomalías el primer día."""
    start_date = datetime(2026, 9, 1, 0, 0)
    readings: list[Reading] = []

    # 14 días con patrón diurno:
    # 00:00 - 05:00: noche (22.0 kWh)
    # 06:00 - 17:00: día (35.0 kWh)
    # 18:00 - 23:00: tarde/noche (28.0 kWh)
    for hour_idx in range(14 * 24):
        ts = start_date + timedelta(hours=hour_idx)
        hour_of_day = ts.hour
        if 0 <= hour_of_day < 6:
            consumption = 22.0
        elif 6 <= hour_of_day < 18:
            consumption = 35.0
        else:
            consumption = 28.0

        readings.append(
            _make_reading(
                meter_id="M-101",
                timestamp=ts,
                consumption=consumption,
                voltage=220.0,
                current=15.0,
                pf=0.95,
            )
        )

    detector = AnomalyDetector()
    results = detector.analyze(
        "M-101",
        readings,
        [],
        analysis_timestamp=datetime(2026, 9, 15, 0, 0),
    )

    assert len(results) == 0


def test_m104_real_pattern_sustained_unfragmented():
    """Valida patrón real M-104: incidente sostenido de varios días con valles nocturnos (2026-09-11 a 2026-09-14).

    Asegura que no se fragmente en múltiples AnomalyRecord por día, retornando len(results) == 1,
    type EXPLAINABLE_ANOMALY y severity MEDIUM.
    """
    import csv
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[4]
    csv_file = repo_root / "readings.csv"

    readings: list[Reading] = []
    with open(csv_file, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["meter_id"] == "M-104":
                readings.append(
                    Reading(
                        meter_id="M-104",
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        consumption_kwh=float(row["consumption_kwh"]),
                        voltage_v=float(row["voltage_v"]),
                        current_a=float(row["current_a"]),
                        power_factor=float(row["power_factor"]),
                    )
                )

    event = Event(
        meter_id="M-104",
        event_timestamp=datetime(2026, 9, 11, 6, 0),
        event_type=EventType.OPERATIONAL_CHANGE,
        description="New production line activated",
    )

    detector = AnomalyDetector()
    results = detector.analyze(
        "M-104",
        readings,
        [event],
        analysis_timestamp=datetime(2026, 9, 15, 0, 0),
    )

    assert len(results) == 1
    record = results[0]
    assert record.type == AnomalyType.EXPLAINABLE_ANOMALY
    assert record.severity == Severity.MEDIUM
    assert "consumption_kwh" in record.evidence.affected_variables
    assert record.evidence.correlated_event == "New production line activated"


def test_full_dataset_matches_expected_patterns():
    """Valida el dataset completo (4.032 filas, 12 medidores, 14 días) contra los 4 casos esperados (PARTE 3).

    Audita que:
    - M-109: exactamente 1 resultado, REAL_ANOMALY, HIGH.
    - M-104: exactamente 1 resultado, EXPLAINABLE_ANOMALY, MEDIUM.
    - M-106: exactamente 1 resultado, FALSE_POSITIVE, LOW.
    - M-112: exactamente 1 resultado, DATA_QUALITY, HIGH.
    E imprime los resultados para los otros 8 medidores para inspección.
    """
    import csv
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[4]
    readings_file = repo_root / "readings.csv"
    events_file = repo_root / "events.csv"

    readings_by_meter: dict[str, list[Reading]] = {}
    with open(readings_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            m = row["meter_id"]
            r = Reading(
                meter_id=m,
                timestamp=datetime.fromisoformat(row["timestamp"]),
                consumption_kwh=float(row["consumption_kwh"]),
                voltage_v=float(row["voltage_v"]),
                current_a=float(row["current_a"]),
                power_factor=float(row["power_factor"]),
            )
            readings_by_meter.setdefault(m, []).append(r)

    events: list[Event] = []
    with open(events_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(
                Event(
                    meter_id=row["meter_id"],
                    event_timestamp=datetime.fromisoformat(row["event_timestamp"]),
                    event_type=EventType(row["event_type"]),
                    description=row["description"],
                )
            )

    detector = AnomalyDetector()
    analysis_ts = datetime(2026, 9, 15, 0, 0)
    all_results: dict[str, list] = {}

    for meter_id in sorted(readings_by_meter.keys()):
        m_readings = readings_by_meter[meter_id]
        m_results = detector.analyze(meter_id, m_readings, events, analysis_ts)
        all_results[meter_id] = m_results

    # 1.d: Assert explícitamente sobre los 4 casos documentados:
    # M-109
    assert len(all_results["M-109"]) == 1
    m109_rec = all_results["M-109"][0]
    assert m109_rec.type == AnomalyType.REAL_ANOMALY
    assert m109_rec.severity == Severity.HIGH

    # M-104
    assert len(all_results["M-104"]) == 1
    m104_rec = all_results["M-104"][0]
    assert m104_rec.type == AnomalyType.EXPLAINABLE_ANOMALY
    assert m104_rec.severity == Severity.MEDIUM

    # M-106
    assert len(all_results["M-106"]) == 1
    m106_rec = all_results["M-106"][0]
    assert m106_rec.type == AnomalyType.FALSE_POSITIVE
    assert m106_rec.severity == Severity.LOW

    # M-112
    assert len(all_results["M-112"]) == 1
    m112_rec = all_results["M-112"][0]
    assert m112_rec.type == AnomalyType.DATA_QUALITY
    assert m112_rec.severity == Severity.HIGH

    # 1.e: Para los otros 8 medidores, imprime cuántas anomalías detecta cada uno
    other_meters = ["M-101", "M-102", "M-103", "M-105", "M-107", "M-108", "M-110", "M-111"]
    print("\n--- Auditoría de los 8 medidores no etiquetados ---")
    for om in other_meters:
        res = all_results.get(om, [])
        print(f"Medidor {om}: {len(res)} anomalías detectadas")
        for rec in res:
            print(f"  [{rec.type.value} | {rec.severity.value} | conf={rec.confidence:.2f}] {rec.evidence.window_start} -> {rec.evidence.window_end} (base={rec.evidence.baseline_kwh}, obs={rec.evidence.observed_kwh}, var={rec.evidence.variation_pct}%)")
    print("--------------------------------------------------\n")






