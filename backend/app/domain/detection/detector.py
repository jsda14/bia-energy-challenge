"""Motor determinista de detección y clasificación de anomalías en medidores."""

from datetime import datetime, timedelta
import statistics

from app.domain.detection.baseline import calculate_baseline
from app.domain.models.anomaly import (
    AnomalyEvidence,
    AnomalyRecord,
    AnomalyType,
    Severity,
)
from app.domain.models.event import Event, EventType
from app.domain.models.reading import Reading


class AnomalyDetector:
    """Motor de detección determinista de anomalías de consumo y calidad eléctrica.

    Analiza lecturas horarias y eventos operativos correlacionando datos cuantitativos
    sin utilizar modelos de lenguaje ni persistencia.
    """

    def __init__(
        self,
        spike_threshold_pct: float = 30.0,
        zscore_threshold: float = 3.0,
        voltage_min_v: float = 200.0,
        voltage_max_v: float = 245.0,
        power_factor_min: float = 0.85,
        lookback_days: int = 7,
        min_history_hours_for_spike_detection: float = 72.0,
        max_consecutive_gap_hours_within_run: float = 8.0,
    ) -> None:
        """Configura los umbrales de detección determinista.

        Args:
            spike_threshold_pct: Porcentaje mínimo de desviación vs baseline para
                considerar un cambio sostenido (RN-02).
            zscore_threshold: Umbral de z-score sobre consumption_kwh para detectar
                outliers puntuales (RN-03).
            voltage_min_v: Límite inferior físico de voltaje en voltios (RN-04).
            voltage_max_v: Límite superior físico de voltaje en voltios (RN-04).
            power_factor_min: Límite inferior aceptable para el factor de potencia (RN-04).
            lookback_days: Cantidad de días hacia atrás a considerar para el cálculo
                de baseline (RN-01).
            min_history_hours_for_spike_detection: Mínimo de horas de historial previo
                requerido para evaluar desviaciones de spike sostenido (RN-02).
            max_consecutive_gap_hours_within_run: Máximo de horas consecutivas por debajo
                del umbral que se toleran dentro de una racha sostenida antes de
                terminarla (RN-02).
        """
        self.spike_threshold_pct = spike_threshold_pct
        self.zscore_threshold = zscore_threshold
        self.voltage_min_v = voltage_min_v
        self.voltage_max_v = voltage_max_v
        self.power_factor_min = power_factor_min
        self.lookback_days = lookback_days
        self.min_history_hours_for_spike_detection = (
            min_history_hours_for_spike_detection
        )
        self.max_consecutive_gap_hours_within_run = (
            max_consecutive_gap_hours_within_run
        )

    def analyze(
        self,
        meter_id: str,
        readings: list[Reading],
        events: list[Event],
        analysis_timestamp: datetime,
    ) -> list[AnomalyRecord]:
        """Analiza el histórico completo de un medidor y clasifica anomalías detectadas.

        Args:
            meter_id: Código del medidor a analizar. Debe coincidir con todas las
                lecturas recibidas.
            readings: Histórico completo de lecturas del medidor en cualquier orden.
            events: Lista de eventos operativos conocidos (puede incluir eventos de
                otros medidores).
            analysis_timestamp: Momento en el que se ejecuta el análisis (fijado en
                `detected_at`).

        Returns:
            Lista de AnomalyRecord detectados y clasificados. Vacía si el medidor
            se encuentra dentro de rangos operativos normales.

        Raises:
            ValueError: Si `readings` está vacío o si alguna lectura posee un
                `meter_id` distinto al parámetro (CB-01, CB-04).
        """
        if not readings:
            raise ValueError("Readings list cannot be empty.")

        for r in readings:
            if r.meter_id != meter_id:
                raise ValueError(
                    f"Reading meter_id '{r.meter_id}' does not match target meter_id '{meter_id}'."
                )

        sorted_readings = sorted(readings, key=lambda r: r.timestamp)
        meter_events = [e for e in events if e.meter_id == meter_id]

        total_readings = len(sorted_readings)
        consumptions = [r.consumption_kwh for r in sorted_readings]
        global_mean_consumption = statistics.mean(consumptions)
        global_std_consumption = (
            statistics.pstdev(consumptions) if total_readings > 1 else 0.0
        )

        raw_candidates: list[dict] = []

        # Fase 1: Detección de anomalías de consumo sostenidas (RN-02) y outliers (RN-03)
        idx = 0
        first_reading_ts = sorted_readings[0].timestamp
        while idx < total_readings:
            reading = sorted_readings[idx]
            history_hours = (
                (reading.timestamp - first_reading_ts).total_seconds() / 3600.0
            )

            if history_hours < self.min_history_hours_for_spike_detection:
                if (
                    global_std_consumption > 0
                    and abs(reading.consumption_kwh - global_mean_consumption)
                    / global_std_consumption
                    >= self.zscore_threshold
                ):
                    raw_candidates.append(
                        {
                            "source": "outlier",
                            "readings": [reading],
                        }
                    )
                idx += 1
                continue

            prior_exists = any(r.timestamp < reading.timestamp for r in sorted_readings)
            if not prior_exists:
                idx += 1
                continue

            try:
                base = calculate_baseline(
                    sorted_readings,
                    reading.timestamp,
                    reading.timestamp,
                    self.lookback_days,
                )
            except ValueError:
                idx += 1
                continue

            dev_pct = (
                ((reading.consumption_kwh - base) / base * 100.0) if base > 0 else 0.0
            )

            if abs(dev_pct) >= self.spike_threshold_pct:
                last_qualifying_idx = idx
                qualifying_count = 1
                curr_idx = idx + 1

                while curr_idx < total_readings:
                    next_reading = sorted_readings[curr_idx]
                    gap_hours = (
                        next_reading.timestamp
                        - sorted_readings[last_qualifying_idx].timestamp
                    ).total_seconds() / 3600.0

                    if gap_hours > self.max_consecutive_gap_hours_within_run:
                        break

                    try:
                        next_base = calculate_baseline(
                            sorted_readings,
                            next_reading.timestamp,
                            next_reading.timestamp,
                            self.lookback_days,
                        )
                    except ValueError:
                        break

                    next_dev = (
                        ((next_reading.consumption_kwh - next_base) / next_base * 100.0)
                        if next_base > 0
                        else 0.0
                    )
                    if abs(next_dev) >= self.spike_threshold_pct:
                        last_qualifying_idx = curr_idx
                        qualifying_count += 1

                    curr_idx += 1

                run_end = last_qualifying_idx + 1
                window_len = run_end - idx

                if window_len >= 3 and qualifying_count >= 3:
                    w_readings = sorted_readings[idx:run_end]
                    raw_candidates.append(
                        {
                            "source": "consumption",
                            "readings": w_readings,
                        }
                    )
                    idx = run_end
                    continue
                else:
                    for k in range(idx, run_end):
                        r_k = sorted_readings[k]
                        if (
                            global_std_consumption > 0
                            and abs(r_k.consumption_kwh - global_mean_consumption)
                            / global_std_consumption
                            >= self.zscore_threshold
                        ):
                            raw_candidates.append(
                                {
                                    "source": "outlier",
                                    "readings": [r_k],
                                }
                            )
                    idx = run_end
                    continue
            else:
                if (
                    global_std_consumption > 0
                    and abs(reading.consumption_kwh - global_mean_consumption)
                    / global_std_consumption
                    >= self.zscore_threshold
                ):
                    raw_candidates.append(
                        {
                            "source": "outlier",
                            "readings": [reading],
                        }
                    )
                idx += 1

        # Fase 2: Detección de inconsistencia eléctrica / calidad de datos (RN-04) independiente
        def is_electrical_invalid(r: Reading) -> bool:
            return (
                r.voltage_v < self.voltage_min_v
                or r.voltage_v > self.voltage_max_v
                or r.power_factor < self.power_factor_min
            )

        electrical_indices = [
            i for i, r in enumerate(sorted_readings) if is_electrical_invalid(r)
        ]

        if electrical_indices:
            clusters: list[list[int]] = []
            current_cluster = [electrical_indices[0]]

            for next_idx in electrical_indices[1:]:
                prev_idx = current_cluster[-1]
                time_diff = (
                    sorted_readings[next_idx].timestamp
                    - sorted_readings[prev_idx].timestamp
                ).total_seconds() / 3600.0
                if time_diff <= 12.0:
                    current_cluster.append(next_idx)
                else:
                    clusters.append(current_cluster)
                    current_cluster = [next_idx]
            clusters.append(current_cluster)

            for cluster in clusters:
                start_i = cluster[0]
                end_i = cluster[-1]
                cluster_readings = sorted_readings[start_i : end_i + 1]

                transitions = sum(
                    1
                    for k in range(1, len(cluster_readings))
                    if is_electrical_invalid(cluster_readings[k])
                    != is_electrical_invalid(cluster_readings[k - 1])
                )
                bad_readings_count = sum(
                    1 for r in cluster_readings if is_electrical_invalid(r)
                )
                bad_ratio = bad_readings_count / len(cluster_readings)

                if transitions >= 1 or bad_ratio >= 0.20:
                    raw_candidates.append(
                        {
                            "source": "data_quality",
                            "readings": cluster_readings,
                        }
                    )

        # Paso de FUSIÓN de ventanas candidatas
        raw_candidates.sort(key=lambda c: c["readings"][0].timestamp)

        merged_candidates: list[dict] = []
        for cand in raw_candidates:
            c_readings = cand["readings"]
            c_start = c_readings[0].timestamp
            c_end = c_readings[-1].timestamp
            c_sources = {cand["source"]}

            if not merged_candidates:
                merged_candidates.append(
                    {
                        "start": c_start,
                        "end": c_end,
                        "sources": c_sources,
                    }
                )
            else:
                prev = merged_candidates[-1]
                gap_hours = (c_start - prev["end"]).total_seconds() / 3600.0
                if c_start <= prev["end"] or gap_hours <= 3.0:
                    prev["end"] = max(prev["end"], c_end)
                    prev["sources"].update(c_sources)
                else:
                    merged_candidates.append(
                        {
                            "start": c_start,
                            "end": c_end,
                            "sources": c_sources,
                        }
                    )

        # Construcción de AnomalyRecord
        records: list[AnomalyRecord] = []

        for candidate in merged_candidates:
            w_start = candidate["start"]
            w_end = candidate["end"]
            w_readings = [
                r for r in sorted_readings if w_start <= r.timestamp <= w_end
            ]
            if not w_readings:
                continue

            prior_readings = [r for r in sorted_readings if r.timestamp < w_start]
            if not prior_readings:
                continue

            baseline_kwh = calculate_baseline(
                sorted_readings, w_start, w_end, self.lookback_days
            )
            observed_kwh = statistics.mean(r.consumption_kwh for r in w_readings)
            variation_pct = (
                ((observed_kwh - baseline_kwh) / baseline_kwh * 100.0)
                if baseline_kwh > 0
                else 0.0
            )

            # Correlación de eventos (RN-05)
            correlated_events = [
                e
                for e in meter_events
                if (w_start - timedelta(hours=24))
                <= e.event_timestamp
                <= w_end
            ]
            closest_event: Event | None = None
            if correlated_events:
                closest_event = min(
                    correlated_events,
                    key=lambda e: abs((e.event_timestamp - w_start).total_seconds()),
                )

            # Clasificación de tipo (RN-04 / RN-05)
            transitions = sum(
                1
                for k in range(1, len(w_readings))
                if is_electrical_invalid(w_readings[k])
                != is_electrical_invalid(w_readings[k - 1])
            )
            has_consumption_anomaly = (
                "consumption" in candidate["sources"]
                or abs(variation_pct) >= self.spike_threshold_pct
            )

            if closest_event and closest_event.event_type == EventType.SCHEDULED_OUTAGE:
                anomaly_type = AnomalyType.FALSE_POSITIVE
            elif closest_event and closest_event.event_type == EventType.OPERATIONAL_CHANGE:
                anomaly_type = AnomalyType.EXPLAINABLE_ANOMALY
            elif closest_event and closest_event.event_type == EventType.DATA_QUALITY:
                anomaly_type = AnomalyType.DATA_QUALITY
            else:
                # Sin evento explicativo (o evento EventType.UNKNOWN)
                if has_consumption_anomaly and transitions == 0:
                    # Degradación sostenida y consistente en la misma dirección como síntoma de sobrecarga (M-109)
                    anomaly_type = AnomalyType.REAL_ANOMALY
                elif "data_quality" in candidate["sources"] or transitions >= 1:
                    # Alta alternancia o inconsistencia de calidad de datos
                    anomaly_type = AnomalyType.DATA_QUALITY
                else:
                    anomaly_type = AnomalyType.REAL_ANOMALY

            # Variables afectadas
            affected_variables: list[str] = []
            if (
                has_consumption_anomaly
                or "outlier" in candidate["sources"]
            ):
                affected_variables.append("consumption_kwh")

            if any(
                r.voltage_v < self.voltage_min_v or r.voltage_v > self.voltage_max_v
                for r in w_readings
            ):
                affected_variables.append("voltage_v")

            # Corriente: variación vs baseline de corriente previa
            prior_currents = [r.current_a for r in prior_readings]
            if prior_currents:
                mean_prior_current = statistics.mean(prior_currents)
                obs_current = statistics.mean(r.current_a for r in w_readings)
                if (
                    mean_prior_current > 0
                    and abs((obs_current - mean_prior_current) / mean_prior_current * 100.0)
                    >= self.spike_threshold_pct
                ):
                    affected_variables.append("current_a")
                elif len(prior_currents) > 1:
                    std_prior_current = statistics.pstdev(prior_currents)
                    if std_prior_current > 0 and any(
                        abs(r.current_a - mean_prior_current) / std_prior_current
                        >= self.zscore_threshold
                        for r in w_readings
                    ):
                        affected_variables.append("current_a")

            if any(r.power_factor < self.power_factor_min for r in w_readings):
                affected_variables.append("power_factor")

            # Severidad (RN-06)
            if anomaly_type == AnomalyType.FALSE_POSITIVE:
                severity = Severity.LOW
            elif anomaly_type == AnomalyType.DATA_QUALITY:
                electrical_out_count = sum(
                    1 for r in w_readings if is_electrical_invalid(r)
                )
                is_strong_electrical = (
                    electrical_out_count / len(w_readings)
                ) > 0.20
                if is_strong_electrical or abs(variation_pct) >= 80.0:
                    severity = Severity.HIGH
                elif abs(variation_pct) >= 30.0:
                    severity = Severity.MEDIUM
                else:
                    severity = Severity.MEDIUM
            elif anomaly_type == AnomalyType.EXPLAINABLE_ANOMALY:
                severity = Severity.MEDIUM
            else:
                has_large_dev = abs(variation_pct) >= 75.0
                has_critical_vars = any(
                    r.voltage_v < 195.0 or r.voltage_v > 250.0 or r.power_factor < 0.75
                    for r in w_readings
                )
                if has_large_dev or has_critical_vars:
                    severity = Severity.HIGH
                elif abs(variation_pct) >= 30.0:
                    severity = Severity.MEDIUM
                else:
                    severity = Severity.LOW

            # Confianza determinista (RN-07)
            duration_hours = max(
                1, int((w_end - w_start).total_seconds() / 3600) + 1
            )
            c_dur = 0.3 * min(1.0, duration_hours / 24.0)

            if anomaly_type == AnomalyType.DATA_QUALITY:
                bad_count = sum(1 for r in w_readings if is_electrical_invalid(r))
                bad_ratio = bad_count / len(w_readings)
                c_mag = 0.3 * min(1.0, bad_ratio * 1.5)
            else:
                c_mag = 0.3 * min(1.0, abs(variation_pct) / 100.0)

            c_base = 0.3
            if closest_event is not None:
                if closest_event.event_type != EventType.UNKNOWN:
                    c_evt = 0.1
                else:
                    c_evt = 0.05
            else:
                c_evt = 0.05 if anomaly_type == AnomalyType.REAL_ANOMALY else 0.0

            confidence = round(max(0.0, min(1.0, c_base + c_dur + c_mag + c_evt)), 2)

            evidence = AnomalyEvidence(
                baseline_kwh=round(baseline_kwh, 2),
                observed_kwh=round(observed_kwh, 2),
                variation_pct=round(variation_pct, 2),
                affected_variables=affected_variables,
                correlated_event=closest_event.description if closest_event else None,
                window_start=w_start,
                window_end=w_end,
            )

            records.append(
                AnomalyRecord(
                    meter_id=meter_id,
                    detected_at=analysis_timestamp,
                    type=anomaly_type,
                    severity=severity,
                    confidence=confidence,
                    evidence=evidence,
                )
            )

        return records
