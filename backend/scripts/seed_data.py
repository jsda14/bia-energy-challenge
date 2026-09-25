"""Script de carga inicial (seed) de datos a partir de readings.csv y events.csv."""

import csv
from datetime import datetime, timezone
from pathlib import Path
import sys

# Asegurar que el directorio backend/ esté en sys.path para ejecuciones directas
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.adapters.outbound.persistence.db import (
    create_all_tables,
    create_db_engine,
    get_session,
)
from app.adapters.outbound.persistence.event_repository import (
    SqlAlchemyEventRepository,
)
from app.adapters.outbound.persistence.meter_repository import (
    SqlAlchemyMeterRepository,
)
from app.adapters.outbound.persistence.reading_repository import (
    SqlAlchemyReadingRepository,
)
from app.config import get_settings
from app.domain.models.event import Event, EventType
from app.domain.models.meter import Meter
from app.domain.models.reading import Reading


def load_readings_csv(csv_path: str) -> list[dict]:
    """Parsea readings.csv y retorna una lista de dicts con tipos convertidos.

    Columnas requeridas: meter_id, timestamp, consumption_kwh, voltage_v,
    current_a, power_factor, status.

    Args:
        csv_path: Ruta al archivo CSV de lecturas.

    Returns:
        Lista de diccionarios con los datos parseados y tipados.

    Raises:
        ValueError: Si alguna fila tiene valores no convertibles (CB-01).
    """
    rows: list[dict] = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader, start=2):
            try:
                meter_id = str(row["meter_id"]).strip()
                # readings.csv no trae sufijo de zona — se asume UTC (mismo
                # supuesto que el resto del backend, que genera todo en UTC).
                timestamp = datetime.fromisoformat(row["timestamp"].strip()).replace(
                    tzinfo=timezone.utc
                )
                consumption_kwh = float(row["consumption_kwh"])
                voltage_v = float(row["voltage_v"])
                current_a = float(row["current_a"])
                power_factor = float(row["power_factor"])
                status = str(row.get("status", "OK")).strip()
            except Exception as exc:
                raise ValueError(
                    f"Error parsing {csv_path} at line {row_idx}: {exc}"
                ) from exc

            rows.append(
                {
                    "meter_id": meter_id,
                    "timestamp": timestamp,
                    "consumption_kwh": consumption_kwh,
                    "voltage_v": voltage_v,
                    "current_a": current_a,
                    "power_factor": power_factor,
                    "status": status,
                }
            )
    return rows


def load_events_csv(csv_path: str) -> list[dict]:
    """Parsea events.csv y retorna una lista de dicts con tipos convertidos.

    Columnas requeridas: meter_id, event_timestamp, event_type, description.

    Args:
        csv_path: Ruta al archivo CSV de eventos.

    Returns:
        Lista de diccionarios con los eventos parseados.

    Raises:
        ValueError: Si alguna fila tiene valores no convertibles (CB-01).
    """
    rows: list[dict] = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader, start=2):
            try:
                meter_id = str(row["meter_id"]).strip()
                # Mismo supuesto que readings.csv: sin sufijo de zona, se
                # asume UTC.
                event_timestamp = datetime.fromisoformat(
                    row["event_timestamp"].strip()
                ).replace(tzinfo=timezone.utc)
                event_type_str = str(row["event_type"]).strip()
                event_type = EventType(event_type_str)
                description = str(row["description"]).strip()
            except Exception as exc:
                raise ValueError(
                    f"Error parsing {csv_path} at line {row_idx}: {exc}"
                ) from exc

            rows.append(
                {
                    "meter_id": meter_id,
                    "event_timestamp": event_timestamp,
                    "event_type": event_type,
                    "description": description,
                }
            )
    return rows


def derive_meters(reading_rows: list[dict]) -> list[dict]:
    """A partir de las filas de readings, deriva la lista de medidores únicos.

    Sintetiza name, location, status y created_at con valores por defecto razonables (RN-03):
    name = meter_id, location = 'Unknown', status = 'active', created_at = primera lectura.

    Args:
        reading_rows: Lista de diccionarios parseados de lecturas.

    Returns:
        Lista de diccionarios representativos de cada medidor único.
    """
    first_timestamps: dict[str, datetime] = {}
    for r in reading_rows:
        m_id = r["meter_id"]
        ts = r["timestamp"]
        if m_id not in first_timestamps or ts < first_timestamps[m_id]:
            first_timestamps[m_id] = ts

    derived: list[dict] = []
    for m_id in sorted(first_timestamps.keys()):
        derived.append(
            {
                "meter_id": m_id,
                "name": m_id,
                "location": "Unknown",
                "status": "active",
                "created_at": first_timestamps[m_id],
            }
        )
    return derived


def seed(
    readings_csv_path: str, events_csv_path: str, database_url: str
) -> None:
    """Orquesta la carga completa de datos a la base de datos de forma idempotente (RN-04).

    Crea tablas si no existen, parsea ambos CSV, deriva medidores, y persiste todo
    a través de los repositorios concretos.

    Args:
        readings_csv_path: Ruta al archivo CSV con las lecturas.
        events_csv_path: Ruta al archivo CSV con los eventos.
        database_url: Cadena de conexión para la base de datos SQLAlchemy.
    """
    engine = create_db_engine(database_url)
    create_all_tables(engine)
    session = get_session(engine)

    try:
        meter_repo = SqlAlchemyMeterRepository(session)
        reading_repo = SqlAlchemyReadingRepository(session)
        event_repo = SqlAlchemyEventRepository(session)

        reading_rows = load_readings_csv(readings_csv_path)
        event_rows = load_events_csv(events_csv_path)
        meter_rows = derive_meters(reading_rows)

        # 1. Persistir medidores
        for m_dict in meter_rows:
            meter = Meter(
                id=m_dict["meter_id"],
                meter_id=m_dict["meter_id"],
                name=m_dict["name"],
                location=m_dict["location"],
                status=m_dict["status"],
            )
            meter_repo.save(meter)

        # 2. Persistir lecturas en lote
        readings = [
            Reading(
                meter_id=r["meter_id"],
                timestamp=r["timestamp"],
                consumption_kwh=r["consumption_kwh"],
                voltage_v=r["voltage_v"],
                current_a=r["current_a"],
                power_factor=r["power_factor"],
                status=r["status"],
            )
            for r in reading_rows
        ]
        reading_repo.save_many(readings)

        # 3. Persistir eventos en lote
        events = [
            Event(
                meter_id=e["meter_id"],
                event_timestamp=e["event_timestamp"],
                event_type=e["event_type"],
                description=e["description"],
            )
            for e in event_rows
        ]
        event_repo.save_many(events)
        
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    repo_root = backend_dir.parent
    readings_file = str(repo_root / "readings.csv")
    events_file = str(repo_root / "events.csv")
    settings = get_settings()

    seed(readings_file, events_file, settings.database_url)

    # Reporte de conteos finales para validación
    engine = create_db_engine(settings.database_url)
    session = get_session(engine)
    try:
        m_repo = SqlAlchemyMeterRepository(session)
        r_repo = SqlAlchemyReadingRepository(session)
        e_repo = SqlAlchemyEventRepository(session)

        all_meters = m_repo.get_all()
        all_events = e_repo.get_all()
        total_readings = sum(
            len(r_repo.get_by_meter_id(m.meter_id)) for m in all_meters
        )

        print("--- Resumen de Seed en Base de Datos ---")
        print(f"Base de datos: {settings.database_url}")
        print(f"Medidores persistidos: {len(all_meters)}")
        print(f"Lecturas persistidas: {total_readings}")
        print(f"Eventos persistidos: {len(all_events)}")
        print("---------------------------------------")
    finally:
        session.close()
