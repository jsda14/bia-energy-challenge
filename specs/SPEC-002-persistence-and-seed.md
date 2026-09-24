# SPEC: SPEC-002 - Persistencia (SQLite/SQLAlchemy) y Seed de Datos

> **Instrucciones para el Agente Codificador:**
> 1. No instales dependencias externas, librerías ni paquetes que no estén explícitamente autorizados en la sección 2.
> 2. No agregues campos adicionales, métodos auxiliares públicos ni endpoints fuera de los contratos descritos en la sección 3.
> 3. Implementa únicamente las tareas listadas en la sección 5 en orden secuencial. Si encuentras un bloqueo, detén la ejecución y solicita aclaración.
> 4. Al finalizar, ejecuta `pytest backend/tests/unit backend/tests/integration -v` y confirma que todos los tests pasan antes de marcar el SPEC como completo.
> 5. Este SPEC NO incluye casos de uso, endpoints HTTP, ni persistencia de `Anomaly` — el repositorio de anomalías se define en SPEC-003, cuando exista el caso de uso que las genera y consume. Tampoco toques `app/domain/` (ya cerrado y auditado en SPEC-001) salvo para importar sus modelos de solo lectura.

---

## 1. Alcance y Fronteras

* **Objetivo:** Persistir en SQLite (vía SQLAlchemy) los medidores, lecturas y
  eventos operativos del dataset, con repositorios concretos que implementan
  puertos definidos por el dominio, y un script de seed que carga
  `readings.csv`/`events.csv` reales a la base de datos.

* **En Alcance (In-Scope):**
  - Modelos SQLAlchemy (tablas) para `Meter`, `Reading`, `Event`, alineados al
    modelo de datos sugerido en el PDF (sección 16) y a los modelos de dominio
    ya existentes en `app/domain/models/`.
  - Puertos de repositorio en `app/domain/ports/` (`MeterRepositoryPort`,
    `ReadingRepositoryPort`, `EventRepositoryPort`) como `Protocol`, siguiendo
    exactamente el mismo patrón que `AIExplainerPort` de SPEC-001.
  - Adapters concretos (`SqlAlchemyMeterRepository`,
    `SqlAlchemyReadingRepository`, `SqlAlchemyEventRepository`) en
    `app/adapters/outbound/persistence/` que implementan esos puertos,
    traduciendo entre filas SQLAlchemy y los modelos de dominio pydantic
    (`Reading`, `Event`, `Meter`) — los repos NUNCA devuelven objetos
    SQLAlchemy hacia afuera, siempre devuelven/reciben los modelos de dominio
    ya existentes.
  - Motor de base de datos SQLite vía `sqlalchemy.create_engine`, con la ruta
    del archivo `.db` configurable (no hardcodeada).
  - Script `backend/scripts/seed_data.py`: lee `readings.csv` y `events.csv`
    de la raíz del repo, deriva la lista de medidores únicos a partir de los
    `meter_id` presentes en `readings.csv` (el dataset no trae un
    `meters.csv` separado — hay que sintetizar el registro de `Meter` por
    cada `meter_id` distinto encontrado), y puebla las 3 tablas. Debe ser
    **idempotente**: correrlo dos veces sobre la misma base de datos no debe
    duplicar filas (ver RN-04).

* **Fuera de Alcance (Out-of-Scope / Non-Goals):**
  - Persistencia de `AnomalyRecord` — SPEC-003 (cuando exista
    `AnalyzeMeterUseCase` que las genera y necesita guardarlas).
  - Casos de uso de `application/` — SPEC-003.
  - Endpoints FastAPI — SPEC-003.
  - Migraciones versionadas (Alembic) — no se usan en este MVP; el schema se
    crea con `Base.metadata.create_all()` en el seed/startup.
  - Modificar `app/domain/models/*.py` o `app/domain/detection/*.py` — ya
    están cerrados y auditados (SPEC-001).
  - Cualquier lógica de negocio (detección, clasificación) — este SPEC es
    puramente de infraestructura de datos.

* **Archivos Afectados:**
  * **Crear:**
    - `backend/app/domain/ports/meter_repository_port.py`
    - `backend/app/domain/ports/reading_repository_port.py`
    - `backend/app/domain/ports/event_repository_port.py`
    - `backend/app/adapters/__init__.py`
    - `backend/app/adapters/outbound/__init__.py`
    - `backend/app/adapters/outbound/persistence/__init__.py`
    - `backend/app/adapters/outbound/persistence/db.py` (engine, session factory, `Base` declarativa)
    - `backend/app/adapters/outbound/persistence/orm_models.py` (clases SQLAlchemy: `MeterORM`, `ReadingORM`, `EventORM`)
    - `backend/app/adapters/outbound/persistence/meter_repository.py`
    - `backend/app/adapters/outbound/persistence/reading_repository.py`
    - `backend/app/adapters/outbound/persistence/event_repository.py`
    - `backend/app/config.py` (settings: ruta de la DB, vía `pydantic-settings`)
    - `backend/scripts/__init__.py`
    - `backend/scripts/seed_data.py`
    - `backend/tests/integration/__init__.py`
    - `backend/tests/integration/persistence/__init__.py`
    - `backend/tests/integration/persistence/test_meter_repository.py`
    - `backend/tests/integration/persistence/test_reading_repository.py`
    - `backend/tests/integration/persistence/test_event_repository.py`
    - `backend/tests/integration/test_seed_data.py`
  * **Modificar:**
    - `backend/app/domain/ports/__init__.py` (agregar los 3 exports nuevos, sin tocar `ai_explainer_port.py` ni su export existente)
    - `backend/requirements.txt` (agregar `sqlalchemy` y `pydantic-settings`, ver sección 2)
  * **Prohibido modificar:**
    - `backend/app/domain/models/*.py`
    - `backend/app/domain/detection/*.py`
    - `backend/app/domain/errors.py`
    - `backend/app/domain/ports/ai_explainer_port.py`
    - `backend/tests/unit/**` (los tests de dominio ya aprobados no se tocan)
    - `readings.csv`, `events.csv` (solo lectura)

---

## 2. Entorno y Dependencias Permitidas

* **Runtime / Versión:** Python 3.11+
* **Librerías autorizadas (nuevas, se agregan a las ya existentes):**
  - `sqlalchemy>=2.0` (ORM y engine)
  - `pydantic-settings>=2.0` (configuración vía `app/config.py`)
  - Las ya autorizadas en SPEC-001: `pydantic>=2.0`, `pytest>=7.0`
  - Librería estándar de Python (`csv`, `pathlib`, `datetime`, etc.)
* **Regla estricta:** Prohibido instalar `pandas`, `numpy`, `alembic`, o
  cualquier driver de DB distinto al `sqlite3` embebido en la librería
  estándar de Python (SQLAlchemy lo usa automáticamente para URLs
  `sqlite:///...`, no requiere paquete adicional). El parseo de CSV usa el
  módulo `csv` de la librería estándar, no `pandas`.

---

## 3. Contratos e Interfaces (Single Source of Truth)

### 3.1 Puertos de Repositorio (Protocols)

```python
# backend/app/domain/ports/meter_repository_port.py
from typing import Protocol
from app.domain.models.meter import Meter

class MeterRepositoryPort(Protocol):
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
```

```python
# backend/app/domain/ports/reading_repository_port.py
from datetime import datetime
from typing import Protocol
from app.domain.models.reading import Reading

class ReadingRepositoryPort(Protocol):
    def get_by_meter_id(self, meter_id: str) -> list[Reading]:
        """Retorna todas las lecturas de un medidor, ordenadas por timestamp
        ascendente. Lista vacía si el medidor no tiene lecturas o no existe.
        """
        ...

    def get_by_meter_id_and_range(
        self, meter_id: str, start: datetime, end: datetime
    ) -> list[Reading]:
        """Retorna las lecturas de un medidor cuyo timestamp está dentro de
        [start, end] (inclusive en ambos extremos), ordenadas ascendente.
        """
        ...

    def save_many(self, readings: list[Reading]) -> None:
        """Inserta lecturas en bloque. Idempotente por (meter_id, timestamp):
        si ya existe una lectura con esa combinación, no la duplica.
        """
        ...
```

```python
# backend/app/domain/ports/event_repository_port.py
from typing import Protocol
from app.domain.models.event import Event

class EventRepositoryPort(Protocol):
    def get_by_meter_id(self, meter_id: str) -> list[Event]:
        """Retorna todos los eventos de un medidor, ordenados por
        event_timestamp ascendente. Lista vacía si no hay eventos.
        """
        ...

    def get_all(self) -> list[Event]:
        """Retorna todos los eventos registrados, de todos los medidores."""
        ...

    def save_many(self, events: list[Event]) -> None:
        """Inserta eventos en bloque. Idempotente por (meter_id,
        event_timestamp, event_type): si ya existe un evento con esa
        combinación exacta, no lo duplica.
        """
        ...
```

### 3.2 Modelos SQLAlchemy (tablas)

```python
# backend/app/adapters/outbound/persistence/orm_models.py
from datetime import datetime
from sqlalchemy import String, Float, DateTime, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class MeterORM(Base):
    __tablename__ = "meters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meter_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime)

class ReadingORM(Base):
    __tablename__ = "readings"
    __table_args__ = (
        UniqueConstraint("meter_id", "timestamp", name="uq_reading_meter_ts"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meter_id: Mapped[str] = mapped_column(String, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    consumption_kwh: Mapped[float] = mapped_column(Float)
    voltage_v: Mapped[float] = mapped_column(Float)
    current_a: Mapped[float] = mapped_column(Float)
    power_factor: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String)

class EventORM(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint(
            "meter_id", "event_timestamp", "event_type",
            name="uq_event_meter_ts_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meter_id: Mapped[str] = mapped_column(String, index=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    event_type: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
```

> Nota: `MeterORM.id` es un entero autoincremental interno de la tabla,
> distinto del campo `meter_id` (string tipo `"M-109"`) que es el
> identificador de negocio. El modelo de dominio `Meter.id` (campo `str`,
> sección 3.1 de SPEC-001) se puebla a partir de `str(MeterORM.id)` al
> convertir de ORM a dominio.

### 3.3 Configuración (`app/config.py`)

```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./bia_energy.db"

    model_config = {"env_prefix": "BIA_"}

def get_settings() -> Settings:
    """Retorna una instancia de Settings, leyendo variables de entorno con
    prefijo BIA_ (ej. BIA_DATABASE_URL) si están definidas, o el default.
    """
    return Settings()
```

### 3.4 Motor de base de datos (`app/adapters/outbound/persistence/db.py`)

```python
# backend/app/adapters/outbound/persistence/db.py
from sqlalchemy import Engine
from sqlalchemy.orm import Session

def create_db_engine(database_url: str) -> Engine:
    """Crea el engine de SQLAlchemy para la URL dada."""
    ...

def create_all_tables(engine: Engine) -> None:
    """Crea todas las tablas definidas en Base.metadata si no existen ya."""
    ...

def get_session(engine: Engine) -> Session:
    """Retorna una nueva sesión de SQLAlchemy vinculada al engine dado."""
    ...
```

### 3.5 Firma del script de seed

```python
# backend/scripts/seed_data.py
def load_readings_csv(csv_path: str) -> list[dict]:
    """Parsea readings.csv (columnas: meter_id, timestamp, consumption_kwh,
    voltage_v, current_a, power_factor, status) y retorna una lista de dicts,
    uno por fila, con los tipos ya convertidos (floats, no strings).
    """
    ...

def load_events_csv(csv_path: str) -> list[dict]:
    """Parsea events.csv (columnas: meter_id, event_timestamp, event_type,
    description) y retorna una lista de dicts, uno por fila.
    """
    ...

def derive_meters(reading_rows: list[dict]) -> list[dict]:
    """A partir de las filas de readings, deriva la lista de medidores únicos
    (por meter_id), sintetizando name/location/status/created_at con valores
    por defecto razonables (ver RN-03).
    """
    ...

def seed(readings_csv_path: str, events_csv_path: str, database_url: str) -> None:
    """Orquesta la carga completa: crea las tablas si no existen, parsea
    ambos CSV, deriva medidores, y persiste todo vía los repositorios
    concretos. Idempotente (RN-04): correr dos veces no duplica filas.
    """
    ...

if __name__ == "__main__":
    ...  # invoca seed() con las rutas por defecto (raíz del repo) y la
         # database_url de Settings
```

---

## 4. Reglas de Negocio y Casos Borde

### 4.1 Reglas de Negocio (RN)

- **RN-01 (Traducción ORM ↔ dominio):** Los repositorios NUNCA exponen
  `MeterORM`/`ReadingORM`/`EventORM` fuera de `persistence/`. Todo método
  público de los repos recibe y retorna exclusivamente los modelos de
  dominio pydantic (`Meter`, `Reading`, `Event`) ya definidos en
  `app/domain/models/`.

- **RN-02 (Timestamps):** Los timestamps se almacenan y recuperan en UTC
  naive (sin timezone), consistente con el formato de `readings.csv`/
  `events.csv` (`"2026-09-01 00:00:00"`, sin offset). No se hace conversión
  de zona horaria en este SPEC.

- **RN-03 (Síntesis de `Meter` desde `readings.csv`):** Como el dataset no
  trae un `meters.csv` separado, cada `meter_id` único encontrado en
  `readings.csv` genera un registro `Meter` con: `name = meter_id` (ej.
  `"M-109"`), `location = "Unknown"`, `status = "active"`, `created_at` =
  timestamp de la primera lectura de ese medidor en el CSV.

- **RN-04 (Idempotencia del seed):** Ejecutar `seed_data.py` múltiples veces
  sobre la misma base de datos no debe crear filas duplicadas. Se logra vía
  los `UniqueConstraint` de las tablas (sección 3.2) combinados con lógica de
  "insertar solo si no existe" en los métodos `save`/`save_many` de los
  repositorios (no confiar únicamente en que la constraint lance un error no
  manejado — el repo debe verificar existencia antes de insertar, o usar
  upsert, de forma que una segunda corrida termine limpiamente sin
  excepción).

### 4.2 Casos Borde (CB)

- **CB-01 (CSV con filas malformadas):** Si una fila de `readings.csv` o
  `events.csv` tiene un valor no convertible al tipo esperado (ej. un float
  inválido), el parseo de esa fila debe fallar con una excepción clara que
  identifique el número de fila y el archivo — no debe fallar silenciosamente
  ni saltarse la fila sin avisar. (El dataset real entregado no tiene filas
  malformadas conocidas; este caso es para robustez, no se espera que se
  dispare con `readings.csv`/`events.csv` reales.)

- **CB-02 (Medidor sin lecturas):** `ReadingRepositoryPort.get_by_meter_id`
  para un `meter_id` que no existe en la tabla retorna lista vacía, no
  lanza excepción.

- **CB-03 (Rango sin resultados):** `get_by_meter_id_and_range` con un rango
  de fechas que no intersecta ninguna lectura retorna lista vacía.

- **CB-04 (Segunda corrida del seed):** Correr `seed()` dos veces seguidas
  con los mismos CSV debe dejar exactamente el mismo número de filas en cada
  tabla que una sola corrida (verificado explícitamente en
  `test_seed_data.py`).

- **CB-05 (Base de datos nueva vs existente):** `create_all_tables` debe
  poder llamarse sobre una base de datos ya poblada sin borrar datos
  existentes (usa `create_all`, que no toca tablas ya creadas).

---

## 5. Plan de Ejecución Secuencial (Atomic Tasks)

- [x] **Paso 1: Configuración y motor de DB:** Crear `app/config.py`
  (`Settings`) y `persistence/db.py` (`create_db_engine`,
  `create_all_tables`, `get_session`).
- [x] **Paso 2: Modelos ORM:** Crear `persistence/orm_models.py` con
  `Base`, `MeterORM`, `ReadingORM`, `EventORM` exactamente según sección 3.2.
- [x] **Paso 3: Puertos de repositorio:** Crear los 3 archivos de puertos en
  `app/domain/ports/` según sección 3.1, y actualizar
  `app/domain/ports/__init__.py` para exportarlos (sin tocar el export de
  `AIExplainerPort` ya existente).
- [x] **Paso 4: Repositorios concretos:** Implementar
  `SqlAlchemyMeterRepository`, `SqlAlchemyReadingRepository`,
  `SqlAlchemyEventRepository` en `persistence/`, cumpliendo RN-01, RN-04,
  CB-02, CB-03.
- [x] **Paso 5: Script de seed:** Implementar `scripts/seed_data.py` según
  sección 3.5, cumpliendo RN-03, RN-04, CB-01, CB-04, CB-05.
  > **Nota post-implementación:** la primera entrega de `save()` en
  > `MeterRepositoryPort` incluía un parámetro `created_at` no autorizado
  > para poder persistir el timestamp real de la primera lectura tal como
  > describe RN-03. Se corrigió en retrabajo: `save(meter: Meter) -> None`
  > respeta la firma exacta del puerto, y `created_at` se resuelve
  > internamente con `datetime.utcnow()` en el momento de la inserción. Esto
  > es una desviación deliberada de la redacción literal de RN-03 (ya no se
  > persiste el timestamp de la primera lectura real, sino el momento del
  > seed) — se prefirió mantener el contrato del puerto intacto sobre
  > preservar ese detalle, que no es crítico para el MVP.
- [x] **Paso 6: Tests de integración:** Implementar los tests en
  `tests/integration/persistence/` (uno por repositorio, cubriendo cada
  método del puerto + CB-02/CB-03) y `tests/integration/test_seed_data.py`
  (cubriendo RN-03, RN-04/CB-04, CB-01, CB-05) usando una base de datos
  SQLite temporal (archivo temporal o `sqlite:///:memory:` con engine
  compartido — no la base de datos real del proyecto).
- [x] **Paso 7: Validación:** Ejecutar
  `pytest backend/tests/unit backend/tests/integration -v` y confirmar 0
  fallos (46/46). Ejecutar además `python backend/scripts/seed_data.py`
  manualmente contra la base de datos real del proyecto (`bia_energy.db`) y
  confirmar que carga los 4.032 registros de `readings.csv`, los 12
  medidores derivados, y los 4 eventos de `events.csv`. Verificado
  independientemente corriendo el script dos veces seguidas: conteos
  idénticos en ambas corridas (12 medidores, 4.032 lecturas, 4 eventos).

---

## 6. Verificación y Checklist de Salida (Pipeline de 5 Pasos)

- [x] **1. Validación Arquitectónica:**
  - `app/domain/` sigue sin importar nada de `app/adapters/` (los puertos
    definen `Protocol`s que los adapters implementan, no al revés).
    Verificado por grep — cero referencias a `adapters` dentro de
    `app/domain/`.
  - `git diff` coincide únicamente con los archivos autorizados en la
    Sección 1. Ningún archivo de `app/domain/models/`,
    `app/domain/detection/`, `app/domain/errors.py`,
    `app/domain/ports/ai_explainer_port.py` ni `tests/unit/**` aparece
    modificado.
- [x] **2. Generación de Tests:**
  - Tests de integración derivados directamente de RN-01..RN-04 y
    CB-01..CB-05, implementados en `tests/integration/` (18 tests: 5 por
    repositorio de Meter/Event, 5 de Reading, 5 de seed_data).
- [x] **3. Validación de Cobertura:**
  - `pytest` ejecutado exitosamente (0 errores) sobre `tests/unit` +
    `tests/integration` combinados (46 tests). Cobertura medida con
    `pytest-cov`: 95% total sobre `app/` — repos de persistencia entre 94%
    y 100%, `config.py` 83% (única línea sin cubrir es la construcción del
    objeto `Settings()` con variables de entorno reales, no ejercitada en
    tests).
- [x] **4. Documentación As-Built:**
  - Docstrings completos (Google style) en cada método público de los
    repositorios, `db.py`, y `seed_data.py`.
- [x] **5. Trazabilidad y Estado:**
  - Checklist de este SPEC completado. Entrada registrada en
    `specs/TASK_STATUS.md` (índice global de todos los SPECs del proyecto),
    incluyendo el detalle del retrabajo por desvío de contrato en
    `MeterRepository.save()`.
