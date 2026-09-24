# SPEC: SPEC-003 - Casos de Uso, Persistencia de Anomalías y API FastAPI

> **Instrucciones para el Agente Codificador:**
> 1. No instales dependencias externas, librerías ni paquetes que no estén explícitamente autorizados en la sección 2.
> 2. No agregues campos adicionales, métodos auxiliares públicos ni endpoints fuera de los contratos descritos en la sección 3.
> 3. Implementa únicamente las tareas listadas en la sección 5 en orden secuencial. Si encuentras un bloqueo, detén la ejecución y solicita aclaración.
> 4. Sigue el **Protocolo de Fronteras de STANDARDS.md sección 2** sin excepción: antes de tocar cualquier archivo, cotéjalo contra la sección 1 de este SPEC; antes de escribir cualquier firma, cotéjala contra la sección 3. Estar autorizado a crear/modificar un archivo NO autoriza a desviarte de las firmas/campos/comportamientos exactos definidos en la sección 3. Si algo no encaja, emite `BLOCKED_BY_BOUNDARY: <archivo/firma> — <razón>` y detente — no lo resuelvas por tu cuenta.
> 5. Al finalizar, ejecuta `pytest backend/tests/unit backend/tests/integration backend/tests/e2e -v` y confirma que todos los tests pasan antes de marcar el SPEC como completo.
> 6. `app/domain/models/`, `app/domain/detection/`, `app/domain/errors.py`, `app/domain/ports/ai_explainer_port.py`, y **todo lo de SPEC-002** (`meter_repository_port.py`, `reading_repository_port.py`, `event_repository_port.py`, sus adapters, `db.py`, `config.py`, `seed_data.py`) ya están cerrados y auditados. No los modifiques salvo lo explícitamente autorizado en la sección 1.

---

## 1. Alcance y Fronteras

* **Objetivo:** Conectar el motor de detección (SPEC-001) con la
  persistencia (SPEC-002) a través de casos de uso de aplicación, exponerlos
  vía una API FastAPI, y persistir las anomalías detectadas. Con esto, el
  sistema queda end-to-end funcional: `POST /ai/analyze` dispara análisis
  real sobre datos reales y `GET /anomalies` devuelve resultados reales con
  explicación en lenguaje natural (vía un adapter de fallback determinista,
  no Claude todavía — eso es SPEC-004).

* **En Alcance (In-Scope):**
  - `AnomalyRepositoryPort` (puerto nuevo) + `AnomalyORM` +
    `SqlAlchemyAnomalyRepository`, siguiendo exactamente el mismo patrón que
    los 3 repositorios de SPEC-002.
  - `TemplateExplainerAdapter`: implementación **real y funcional** (no un
    mock de test) de `AIExplainerPort` que genera `reason` y
    `recommended_action` mediante plantillas de texto determinista a partir
    de los datos de `AnomalyEvidence` — sin llamar a ningún LLM. Es el
    fallback que `ARCHITECTURE.md` §4 exige que exista siempre;
    `ClaudeExplainerAdapter` (SPEC-004) lo reusará como fallback cuando la
    API falle.
  - `AnalysisRun`: modelo de dominio + tabla nueva que registra cada
    ejecución de análisis (uno o todos los medidores) con id, estado,
    timestamp, y resultado — preparado para que `GET /ai/analysis/:id`
    funcione ya, aunque hoy la ejecución sea síncrona (ver RN-05).
  - Casos de uso en `app/application/`: `AnalyzeMeterUseCase`,
    `GetDashboardSummaryUseCase`, `ListMetersUseCase`, `GetMeterDetailUseCase`,
    `ListAnomaliesUseCase`, `GetAnomalyDetailUseCase`.
  - Endpoints FastAPI en `app/adapters/inbound/api/`, exactamente los 8 de
    `ARCHITECTURE.md` §6.
  - `app/main.py`: composition root — construye engine, repos concretos,
    `TemplateExplainerAdapter`, casos de uso, y los inyecta en los routers.
  - Tests e2e con `TestClient` de FastAPI.

* **Fuera de Alcance (Out-of-Scope / Non-Goals):**
  - `ClaudeExplainerAdapter` real (SDK de Anthropic, agentic loop, MCP
    `EventQueryTool`) — SPEC-004.
  - Ejecución asíncrona real de análisis (background tasks, colas) — el
    análisis corre síncrono dentro del request HTTP; `AnalysisRun` solo dejó
    la estructura de datos lista, no implica async todavía (RN-05).
  - Autenticación/autorización — no forma parte del MVP (ver
    `ARCHITECTURE.md` §9).
  - Frontend — SPECs posteriores.
  - Modificar el algoritmo de `AnomalyDetector` o `calculate_baseline` — ya
    cerrados en SPEC-001.

* **Archivos Afectados:**
  * **Crear:**
    - `backend/app/domain/models/anomaly_run.py` (modelo `AnalysisRun`)
    - `backend/app/domain/ports/anomaly_repository_port.py`
    - `backend/app/domain/ports/anomaly_run_repository_port.py`
    - `backend/app/adapters/outbound/persistence/anomaly_orm.py` (o agregar `AnomalyORM`/`AnalysisRunORM` a `orm_models.py` — ver nota en sección 3.2)
    - `backend/app/adapters/outbound/persistence/anomaly_repository.py`
    - `backend/app/adapters/outbound/persistence/anomaly_run_repository.py`
    - `backend/app/adapters/outbound/ai/__init__.py`
    - `backend/app/adapters/outbound/ai/template_explainer_adapter.py`
    - `backend/app/adapters/inbound/__init__.py`
    - `backend/app/adapters/inbound/api/__init__.py`
    - `backend/app/adapters/inbound/api/schemas.py` (DTOs Pydantic de request/response)
    - `backend/app/adapters/inbound/api/dependencies.py` (funciones stub
      tipadas para `Depends(...)` en los routers, sobreescritas en
      `main.py` vía `app.dependency_overrides` — ver sección 3.7)
    - `backend/app/adapters/outbound/persistence/db_state.py` (dueño único
      del `Engine` global de la app, para que `dependencies.py` no necesite
      importar desde `app/main.py` — ver sección 3.7 punto 0)
    - `backend/app/adapters/inbound/api/meters_router.py`
    - `backend/app/adapters/inbound/api/anomalies_router.py`
    - `backend/app/adapters/inbound/api/dashboard_router.py`
    - `backend/app/adapters/inbound/api/ai_router.py`
    - `backend/app/application/__init__.py`
    - `backend/app/application/analyze_meter.py`
    - `backend/app/application/get_dashboard_summary.py`
    - `backend/app/application/list_meters.py`
    - `backend/app/application/get_meter_detail.py`
    - `backend/app/application/list_anomalies.py`
    - `backend/app/application/get_anomaly_detail.py`
    - `backend/app/main.py`
    - `backend/tests/unit/application/__init__.py`
    - `backend/tests/unit/application/test_analyze_meter.py`
    - `backend/tests/unit/adapters/__init__.py`
    - `backend/tests/unit/adapters/test_template_explainer_adapter.py`
    - `backend/tests/integration/persistence/test_anomaly_repository.py`
    - `backend/tests/integration/persistence/test_anomaly_run_repository.py`
    - `backend/tests/e2e/__init__.py`
    - `backend/tests/e2e/test_api.py`
  * **Modificar:**
    - `backend/app/domain/ports/__init__.py` (agregar exports de
      `AnomalyRepositoryPort`, `AnomalyRunRepositoryPort`, sin tocar los
      exports existentes de SPEC-001/SPEC-002)
    - `backend/requirements.txt` (agregar `fastapi`, `uvicorn`, `httpx` — ver
      sección 2; `httpx` es requerido por `TestClient` de FastAPI para tests)
    - `backend/app/adapters/outbound/persistence/meter_repository.py`,
      `reading_repository.py`, `event_repository.py`, `scripts/seed_data.py`
      — **excepcionalmente autorizado, solo para el cambio de la sección
      3.8** (quitar `session.commit()` de los repos, mover el commit al
      ciclo de vida del request / al script de seed). Ningún otro
      comportamiento de estos archivos cambia — ver sección 3.8 para el
      detalle exacto y la justificación de por qué se reabre SPEC-002.
  * **Prohibido modificar:**
    - `backend/app/domain/models/meter.py`, `reading.py`, `event.py`,
      `anomaly.py` (SPEC-001, cerrado)
    - `backend/app/domain/detection/*.py` (SPEC-001, cerrado)
    - `backend/app/domain/errors.py`
    - `backend/app/domain/ports/ai_explainer_port.py`,
      `meter_repository_port.py`, `reading_repository_port.py`,
      `event_repository_port.py` (contratos ya cerrados)
    - `backend/app/adapters/outbound/persistence/db.py`, `orm_models.py`
      (SPEC-002, cerrado — salvo agregar las clases ORM nuevas si decides
      ponerlas en `orm_models.py` en vez de un archivo aparte, ver nota
      sección 3.2; en ese caso solo AGREGAS clases, no tocas
      `MeterORM`/`ReadingORM`/`EventORM` existentes)
    - `backend/app/config.py`
    - `backend/scripts/seed_data.py`
    - `backend/tests/unit/domain/**`, `backend/tests/integration/persistence/test_meter_repository.py`, `test_reading_repository.py`, `backend/tests/integration/test_seed_data.py` (ya aprobados)
    - `readings.csv`, `events.csv`

---

## 2. Entorno y Dependencias Permitidas

* **Runtime / Versión:** Python 3.11+
* **Librerías autorizadas (nuevas, se agregan a las ya existentes):**
  - `fastapi>=0.110`
  - `uvicorn[standard]>=0.29` (servidor ASGI para correr la app; no se usa en
    tests, pero se agrega para que `README.md` de una futura entrega pueda
    documentar cómo levantar el servidor)
  - `httpx>=0.27` (requerido internamente por `fastapi.testclient.TestClient`)
  - Las ya autorizadas en SPEC-001/SPEC-002: `pydantic>=2.0`, `pytest>=7.0`,
    `sqlalchemy>=2.0`, `pydantic-settings>=2.0`
* **Regla estricta:** Prohibido instalar `celery`, `redis`, cualquier cola de
  tareas, cualquier SDK de Anthropic/OpenAI/LLM (eso es SPEC-04), o
  `alembic`. Sin websockets ni streaming.

---

## 3. Contratos e Interfaces (Single Source of Truth)

### 3.1 Modelo de dominio nuevo: `AnalysisRun`

```python
# backend/app/domain/models/anomaly_run.py
from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class AnalysisRunStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisRun(BaseModel):
    """Registro inmutable de una ejecución de análisis de anomalías.

    Attributes:
        id: Identificador único de la ejecución (UUID como string).
        requested_meter_id: meter_id específico solicitado, o None si fue
            "analizar todos los medidores".
        status: Estado final de la ejecución (este SPEC solo produce
            resultados síncronos, por lo que status siempre es COMPLETED o
            FAILED al momento de crear el registro — no existe estado
            intermedio "RUNNING" en este SPEC).
        started_at: Momento en que se inició el análisis.
        finished_at: Momento en que terminó el análisis.
        anomalies_detected_count: Cantidad total de AnomalyRecord generados
            en esta ejecución (0 o más).
        error_message: Detalle del error si status es FAILED, None si
            status es COMPLETED.
    """

    model_config = {"frozen": True}

    id: str
    requested_meter_id: str | None
    status: AnalysisRunStatus
    started_at: datetime
    finished_at: datetime
    anomalies_detected_count: int
    error_message: str | None = None
```

### 3.2 Puertos de Repositorio nuevos

> **IMPORTANTE — leer antes de implementar:** `AnomalyRecord` (SPEC-001,
> cerrado) no tiene `id`, `reason` ni `recommended_action` — esos campos no
> existen en su modelo pydantic y este SPEC no puede agregarlos (tocar
> `app/domain/models/anomaly.py` está prohibido). Por eso los métodos de
> LECTURA del puerto (`get_all`, `get_by_id`, `get_by_meter_id`) NO pueden
> retornar `AnomalyRecord` — retornan `PersistedAnomaly` (sección 3.1-bis,
> justo abajo), un modelo de dominio nuevo que sí incluye esos campos. Solo
> `save_many` (que recibe datos, no los retorna) sigue trabajando con
> `AnomalyRecord` de entrada, tal como corrige la nota de la sección 3.3.

### 3.1-bis Modelo de dominio nuevo: `PersistedAnomaly`

```python
# backend/app/domain/models/anomaly.py (agregar a este archivo — SÍ está
# permitido AGREGAR una clase nueva aquí, lo prohibido es MODIFICAR
# AnomalyType/Severity/AnomalyEvidence/AnomalyRecord ya existentes)
from pydantic import BaseModel, Field


class PersistedAnomaly(BaseModel):
    """Una AnomalyRecord ya persistida, con su id de almacenamiento y su
    explicación en lenguaje natural ya generada. Distinto de AnomalyRecord:
    representa 'una anomalía guardada y explicada', no 'una anomalía recién
    detectada por el dominio' — id/reason/recommended_action solo existen
    una vez que se persiste (SPEC-003), el AnomalyDetector (SPEC-001) nunca
    los produce.

    Attributes:
        id: Identificador único de persistencia (UUID como string),
            asignado por el repositorio al guardar.
        record: El AnomalyRecord original detectado por el dominio.
        reason: Explicación en lenguaje natural (de AIExplanation.reason).
        recommended_action: Acción recomendada (de
            AIExplanation.recommended_action).
    """

    model_config = {"frozen": True}

    id: str
    record: AnomalyRecord
    reason: str
    recommended_action: str
```

```python
# backend/app/domain/ports/anomaly_repository_port.py
from typing import Protocol
from app.domain.models.anomaly import AnomalyRecord, PersistedAnomaly
from app.domain.ports.ai_explainer_port import AIExplanation

class AnomalyRepositoryPort(Protocol):
    def get_all(self) -> list[PersistedAnomaly]:
        """Retorna todas las anomalías persistidas, sin filtros, ordenadas
        por record.detected_at descendente (más reciente primero).
        """
        ...

    def get_by_id(self, anomaly_id: str) -> PersistedAnomaly | None:
        """Retorna la anomalía cuyo id coincide, o None si no existe."""
        ...

    def get_by_meter_id(self, meter_id: str) -> list[PersistedAnomaly]:
        """Retorna las anomalías de un medidor, ordenadas por
        record.detected_at descendente. Lista vacía si no hay anomalías
        para ese medidor.
        """
        ...

    def save_many(
        self, items: list[tuple[AnomalyRecord, AIExplanation]]
    ) -> list[str]:
        """Persiste una lista de (AnomalyRecord, AIExplanation) y retorna
        la lista de ids generados (mismo orden que la lista de entrada).
        Cada llamada crea registros nuevos — no hay concepto de "actualizar"
        una anomalía existente en este SPEC (cada corrida de análisis genera
        entradas nuevas, no es idempotente como los repos de SPEC-002).
        """
        ...
```

> Esta es ahora la única definición vigente de `AnomalyRepositoryPort` — ya
> incorpora la corrección de `save_many` que antes vivía como nota aparte en
> la sección 3.3. La sección 3.3 ya no necesita repetir esa corrección (ver
> nota actualizada ahí).

```python
# backend/app/domain/ports/anomaly_run_repository_port.py
from typing import Protocol
from app.domain.models.anomaly_run import AnalysisRun

class AnomalyRunRepositoryPort(Protocol):
    def save(self, run: AnalysisRun) -> None:
        """Persiste una ejecución de análisis. run.id ya viene asignado por
        el caller (el caso de uso genera el UUID antes de llamar save)."""
        ...

    def get_by_id(self, run_id: str) -> AnalysisRun | None:
        """Retorna la ejecución cuyo id coincide, o None si no existe."""
        ...
```

### 3.3 Modelos ORM nuevos

```python
# Agregar a orm_models.py (o a un archivo nuevo anomaly_orm.py que importe
# Base desde orm_models.py — a tu criterio, documenta cuál elegiste)
from sqlalchemy import String, Float, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

class AnomalyORM(Base):
    __tablename__ = "anomalies"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # UUID string
    meter_id: Mapped[str] = mapped_column(String, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    type: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String)
    recommended_action: Mapped[str] = mapped_column(String)
    baseline_kwh: Mapped[float] = mapped_column(Float)
    observed_kwh: Mapped[float] = mapped_column(Float)
    variation_pct: Mapped[float] = mapped_column(Float)
    affected_variables: Mapped[str] = mapped_column(String)  # CSV: "consumption_kwh,voltage_v"
    correlated_event: Mapped[str | None] = mapped_column(String, nullable=True)
    window_start: Mapped[datetime] = mapped_column(DateTime)
    window_end: Mapped[datetime] = mapped_column(DateTime)

class AnalysisRunORM(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # UUID string
    requested_meter_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime] = mapped_column(DateTime)
    anomalies_detected_count: Mapped[int] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
```

> `AnomalyRecord` (dominio) no tiene `id`, `reason` ni `recommended_action`;
> `AnomalyORM` (persistencia) sí los tiene como columnas. El repo concreto es
> responsable de: al guardar (`save_many`), generar el id (RN-02) y
> serializar `AnomalyEvidence.affected_variables` a CSV (RN-03); al leer
> (`get_all`/`get_by_id`/`get_by_meter_id`), reconstruir un
> `PersistedAnomaly` completo — deserializando `affected_variables` de
> vuelta a `list[str]`, reconstruyendo el `AnomalyRecord`/`AnomalyEvidence`
> anidado desde las columnas correspondientes, y envolviendo todo junto con
> `id`, `reason`, `recommended_action` tal como define `PersistedAnomaly`
> (sección 3.1-bis).

### 3.4 Adapter de explicación por plantilla

```python
# backend/app/adapters/outbound/ai/template_explainer_adapter.py
from app.domain.models.anomaly import AnomalyRecord, AnomalyType
from app.domain.ports.ai_explainer_port import AIExplanation, AIExplainerPort

class TemplateExplainerAdapter(AIExplainerPort):
    """Fallback determinista de AIExplainerPort: genera reason y
    recommended_action con plantillas de texto a partir de AnomalyEvidence,
    sin llamar a ningún servicio externo. Es el fallback que
    ClaudeExplainerAdapter (SPEC-004) reutilizará cuando la API falle.
    """

    def explain(self, anomaly: AnomalyRecord) -> AIExplanation:
        """Genera explicación determinista según el tipo de anomalía.

        Args:
            anomaly: Registro de anomalía clasificada por el dominio.

        Returns:
            AIExplanation con una plantilla de texto que referencia los
            datos concretos de evidence (variation_pct, affected_variables,
            correlated_event) — nunca un texto genérico sin datos.
        """
        ...
```

> Plantillas por `AnomalyType` (RN-04 define el contenido exacto esperado de
> cada plantilla — implementa 4 ramas, una por valor del enum).

### 3.5 Casos de Uso

```python
# backend/app/application/analyze_meter.py
from app.domain.models.anomaly_run import AnalysisRun
from app.domain.ports.ai_explainer_port import AIExplainerPort
from app.domain.ports.anomaly_repository_port import AnomalyRepositoryPort
from app.domain.ports.anomaly_run_repository_port import AnomalyRunRepositoryPort
from app.domain.ports.event_repository_port import EventRepositoryPort
from app.domain.ports.meter_repository_port import MeterRepositoryPort
from app.domain.ports.reading_repository_port import ReadingRepositoryPort
from app.domain.detection.detector import AnomalyDetector

class AnalyzeMeterUseCase:
    """Orquesta un ciclo completo de análisis: lee datos, detecta anomalías,
    genera explicaciones, y persiste resultados. Composición explícita de
    puertos — no importa ningún adapter concreto.
    """

    def __init__(
        self,
        meter_repo: MeterRepositoryPort,
        reading_repo: ReadingRepositoryPort,
        event_repo: EventRepositoryPort,
        anomaly_repo: AnomalyRepositoryPort,
        run_repo: AnomalyRunRepositoryPort,
        explainer: AIExplainerPort,
        detector: AnomalyDetector,
    ) -> None:
        """Inyecta las dependencias necesarias para ejecutar el análisis."""
        ...

    def execute(self, meter_id: str | None = None) -> AnalysisRun:
        """Ejecuta el análisis para un medidor específico, o para todos los
        medidores registrados si meter_id es None.

        Args:
            meter_id: Código del medidor a analizar, o None para analizar
                todos los medidores registrados vía meter_repo.get_all().

        Returns:
            AnalysisRun con el resultado consolidado de la ejecución.
            status=FAILED si meter_id fue provisto pero no existe ningún
            medidor con ese meter_id (RN-06); en cualquier otro escenario de
            error de un medidor individual dentro de un análisis "todos los
            medidores", ver RN-07.
        """
        ...
```

> Los otros 5 casos de uso (`GetDashboardSummaryUseCase`, `ListMetersUseCase`,
> `GetMeterDetailUseCase`, `ListAnomaliesUseCase`, `GetAnomalyDetailUseCase`)
> son de solo lectura: reciben los puertos de repositorio que necesitan en
> `__init__`, y un único método `execute(...)` que retorna los datos
> agregados/filtrados que su endpoint correspondiente necesita (ver sección
> 3.6 para la forma exacta de cada response). No implementan lógica de
> negocio nueva — solo orquestan llamadas a los repos y arman el DTO de
> salida. Implementa sus firmas siguiendo el mismo patrón mostrado arriba
> (constructor con puertos inyectados, método `execute`), infiriendo los
> parámetros de `execute` a partir de qué necesita cada endpoint de la
> sección 3.6.

### 3.6 Endpoints FastAPI y Schemas

Los 8 endpoints de `ARCHITECTURE.md` §6, implementados exactamente así:

```
POST /ai/analyze          body: {"meter_id": str | null}  → AnalysisRunResponse
GET  /ai/analysis/{id}                                     → AnalysisRunResponse
GET  /dashboard/summary                                    → DashboardSummaryResponse
GET  /meters              query: ?status=&search=&sort_by= → list[MeterSummaryResponse]
GET  /meters/{meterId}                                     → MeterDetailResponse
GET  /meters/{meterId}/readings                             → list[ReadingResponse]
GET  /anomalies           query: ?severity=&type=           → list[AnomalySummaryResponse]
GET  /anomalies/{id}                                        → AnomalyDetailResponse
```

```python
# backend/app/adapters/inbound/api/schemas.py
from datetime import datetime
from pydantic import BaseModel

class AnalysisRunResponse(BaseModel):
    id: str
    requested_meter_id: str | None
    status: str
    started_at: datetime
    finished_at: datetime
    anomalies_detected_count: int
    error_message: str | None = None

class DashboardSummaryResponse(BaseModel):
    total_meters: int
    total_consumption_kwh: float
    anomalies_detected: int
    high_priority_count: int
    average_confidence: float | None  # None si no hay anomalías persistidas
    last_analysis_at: datetime | None  # None si nunca se corrió un análisis

class MeterSummaryResponse(BaseModel):
    meter_id: str
    name: str
    status: str  # "OK" | "Alert" | "Critical", derivado según RN-08
    consumption_kwh: float  # consumo total del período disponible
    variation_pct: float  # variación vs baseline del período más reciente
    anomaly_severity: str | None  # severidad de la anomalía más reciente, None si no tiene

class ReadingResponse(BaseModel):
    timestamp: datetime
    consumption_kwh: float
    voltage_v: float
    current_a: float
    power_factor: float
    status: str

class MeterDetailResponse(BaseModel):
    meter_id: str
    name: str
    location: str
    status: str
    consumption_kwh: float
    baseline_kwh: float | None  # None si no hay suficiente historial (CB del SPEC-001)
    variation_pct: float | None
    readings: list[ReadingResponse]

class AnomalySummaryResponse(BaseModel):
    id: str
    meter_id: str
    type: str
    severity: str
    confidence: float
    recommended_action: str
    detected_at: datetime

class AnomalyDetailResponse(BaseModel):
    id: str
    meter_id: str
    type: str
    severity: str
    confidence: float
    reason: str
    recommended_action: str
    baseline_kwh: float
    observed_kwh: float
    variation_pct: float
    affected_variables: list[str]
    correlated_event: str | None
    window_start: datetime
    window_end: datetime
```

> Los routers (`meters_router.py`, `anomalies_router.py`,
> `dashboard_router.py`, `ai_router.py`) solo parsean/validan input, llaman
> al caso de uso correspondiente inyectado, y serializan su resultado al
> schema de respuesta (`STANDARDS.md` §3: "nada de lógica de negocio en
> routers"). Usa `fastapi.Depends` para la inyección de los casos de uso
> desde `app/main.py`.

### 3.7 Composition root: sesión de base de datos compartida por request

> **Corrección post-implementación (2026-09-24):** la primera entrega de
> este SPEC tenía cada `get_X_repo()` en `main.py` abriendo su propia
> `Session` de SQLAlchemy independiente (una por repo, no compartida). Esto
> significa que dentro de un mismo `AnalyzeMeterUseCase.execute()`,
> `anomaly_repo.save_many()` y `run_repo.save()` hacían `commit()` en
> sesiones distintas — sin atomicidad entre persistir las anomalías
> detectadas y persistir el `AnalysisRun` que las resume. Si el proceso
> fallaba entre ambos commits, quedaban anomalías huérfanas sin su
> `AnalysisRun` correspondiente. Este SPEC ahora exige explícitamente el
> patrón "una sesión por request" de FastAPI para evitarlo.

**Patrón requerido:**

0. **Primero, elimina el ciclo de import antes de tocar `dependencies.py`:**
   `get_db_session()` necesita el `Engine` de la aplicación, pero
   `dependencies.py` NO puede importar `app/main.py` (eso crearía un ciclo:
   `main.py` ya importa `dependencies.py` para registrar los
   `dependency_overrides`). La solución es que el `Engine` global deje de
   vivir en `main.py`: créalo (o muévelo, si ya existe como variable global
   en `main.py`) a un módulo nuevo y pequeño,
   `app/adapters/outbound/persistence/db_state.py`, con una función
   `get_or_create_engine() -> Engine` que crea el engine la primera vez que
   se llama (usando `create_db_engine`/`get_settings`) y reutiliza la misma
   instancia en llamadas subsecuentes (un simple `global _engine` con
   verificación `if _engine is None`, sin necesidad de nada más
   sofisticado). Tanto `main.py` (en el evento de startup) como
   `dependencies.py` (dentro de `get_db_session`) importan
   `get_or_create_engine` desde `db_state.py` — nunca uno del otro. Esto no
   está en la lista original de "Archivos Afectados" del SPEC, pero queda
   autorizado explícitamente aquí como parte de este mismo retrabajo (no
   hace falta `BLOCKED_BY_BOUNDARY` para este archivo específico).

1. `app/adapters/inbound/api/dependencies.py` define una función
   `get_db_session() -> Generator[Session, None, None]` (generador,
   usando `yield`, siguiendo el patrón estándar de FastAPI para recursos
   con ciclo de vida) que abre UNA `Session` nueva por request usando
   `get_or_create_engine()` de `db_state.py` (nunca importando desde
   `app/main.py`), la entrega vía `yield`, y la cierra en un bloque
   `finally` al terminar el request (sin hacer commit ni rollback
   automático ahí — cada caso de uso/repo es responsable de su propio
   commit, igual que ya hacen los repos de SPEC-002).

2. `dependencies.py` también define las funciones stub tipadas para cada
   caso de uso (`get_analyze_meter_use_case`, `get_dashboard_summary_use_case`,
   etc. — una por cada uno de los 6 casos de uso de la sección 3.5), cada
   una con la firma `def get_X_use_case() -> XUseCase: raise
   NotImplementedError` (nunca se ejecutan de verdad; son marcadores de tipo
   para que los routers usen `Depends(get_X_use_case)` sin importar nada de
   `app/main.py` ni de los adapters concretos).

3. `app/main.py` (composition root) es quien:
   - Define una función `build_X_use_case(session: Session = Depends(get_db_session)) -> XUseCase`
     por cada caso de uso — esta función SÍ recibe la sesión compartida vía
     `Depends(get_db_session)`, construye TODOS los repos concretos que ese
     caso de uso necesita pasándoles la MISMA instancia de `session` (no
     `get_engine()` cada vez), y arma el caso de uso con esos repos.
   - Registra `app.dependency_overrides[stub_X] = build_X_use_case` para
     cada uno de los 6 casos de uso, igual que ya hace hoy para los stubs
     de casos de uso — la diferencia es que ahora `build_X_use_case` en sí
     mismo depende de `get_db_session` vía `Depends`, encadenando la
     resolución de dependencias de FastAPI en vez de crear sesiones sueltas
     con `get_engine()` directo dentro de cada `get_X_repo()`.

4. Los repos concretos (`SqlAlchemyMeterRepository`, etc.) NO cambian su
   firma — ya aceptan `Session | Engine` en el constructor desde SPEC-002 y
   SPEC-003; simplemente ahora siempre reciben una `Session` ya abierta
   (nunca un `Engine` crudo) desde el composition root.

### 3.8 Corrección post-implementación: el `commit()` sale de los repos

> **Corrección post-implementación #2 (2026-09-24):** la sección 3.7 logró
> que todos los repos de un mismo caso de uso compartan una `Session`, pero
> eso por sí solo NO da atomicidad si cada repo sigue confirmando su propia
> transacción. Se verificó que los 5 repos que hacen escritura
> (`SqlAlchemyMeterRepository.save`, `SqlAlchemyReadingRepository.save_many`,
> `SqlAlchemyEventRepository.save_many` — los 3 de SPEC-002 — más
> `SqlAlchemyAnomalyRepository.save_many` y
> `SqlAlchemyAnomalyRunRepository.save` de este SPEC) llaman cada uno
> `self._session.commit()` internamente. Esto significa que aunque
> `anomaly_repo` y `run_repo` compartan sesión, el primer `commit()` ya
> confirma esa escritura en disco antes de que el segundo repo corra — si
> el proceso falla entre ambos, la primera escritura queda persistida sin
> la segunda. La sesión compartida es condición necesaria pero no
> suficiente para atomicidad; también hace falta que nadie confirme la
> transacción hasta que TODA la operación (todos los repos involucrados)
> haya terminado.

**Autorización explícita para reabrir SPEC-002 (excepcional):** este SPEC
autoriza modificar los 3 repos de SPEC-002
(`meter_repository.py`/`reading_repository.py`/`event_repository.py`) — que
en la sección 1 de este mismo SPEC-003 estaban listados como "Prohibido
modificar" — **únicamente** para el cambio descrito abajo (quitar
`session.commit()`, nada más). Ningún otro comportamiento de esos 3 repos
cambia. Esta es la primera vez que un SPEC posterior reabre código de un
SPEC ya cerrado; se documenta aquí para que quede explícito por qué está
autorizado, en vez de dejarlo implícito.

**Cambio requerido, en los 5 repos de escritura:**

1. Reemplaza cada `self._session.commit()` por `self._session.flush()`.
   `flush()` envía los `INSERT`/`UPDATE` pendientes a la conexión de base de
   datos (para que consultas subsecuentes DENTRO de la misma transacción ya
   vean los cambios, necesario para que la lógica de idempotencia — "leer
   antes de escribir" — siga funcionando exactamente igual que hoy), pero
   NO confirma la transacción. El `commit()` real ahora ocurre en un solo
   lugar, fuera de los repos:

2. En `app/adapters/inbound/api/dependencies.py`,
   `get_db_session()` hace el `commit()` final, después del `yield`, solo
   si el request completo terminó sin excepción:

   ```python
   def get_db_session() -> Generator[Session, None, None]:
       session = get_session(get_or_create_engine())
       try:
           yield session
           session.commit()
       except Exception:
           session.rollback()
           raise
       finally:
           session.close()
   ```

   Esto es lo que da atomicidad real: si `AnalyzeMeterUseCase.execute()`
   lanza una excepción después de que `anomaly_repo.save_many()` ya hizo su
   `flush()` pero antes de que `run_repo.save()` corra, ninguno de los dos
   queda confirmado — el `except`/`rollback()` deshace todo lo que estaba
   pendiente en la sesión.

3. `backend/scripts/seed_data.py` NO pasa por `get_db_session()` (es un
   script standalone, no un request de FastAPI), así que debe hacer su
   propio `session.commit()` explícito. Agrega
   `session.commit()` al final de la función `seed()` (después de las 3
   llamadas a los repos — `meter_repo.save(...)` en el loop,
   `reading_repo.save_many(...)`, `event_repo.save_many(...)` — y antes del
   `finally: session.close()` que ya existe). Esta es la única línea nueva
   autorizada en `seed_data.py`; el resto del archivo no cambia.

4. Ningún test existente de idempotencia (`test_save_idempotence`,
   `test_save_many_idempotency`, `test_cb07_double_run`, etc.) debería
   necesitar cambios — la idempotencia depende de la lógica de "verificar
   existencia antes de insertar" dentro de cada repo, que no cambia; solo
   cambia CUÁNDO se confirma la transacción, no CÓMO se decide si insertar.
   Si algún test SÍ dependía implícitamente de que el repo hiciera commit
   (por ejemplo, abriendo una segunda sesión/conexión distinta para
   verificar que los datos "ya están ahí"), ajústalo para que verifique
   dentro de la misma sesión, o haga su propio commit explícito en el
   setup del test antes de verificar — sin cambiar la intención original
   del test.

---

## 4. Reglas de Negocio y Casos Borde

### 4.1 Reglas de Negocio (RN)

- **RN-01 (Orquestación de `AnalyzeMeterUseCase`):** Para cada medidor a
  analizar: 1) leer sus `Reading` y `Event` vía los repos, 2) llamar
  `AnomalyDetector.analyze()`, 3) para cada `AnomalyRecord` resultante,
  llamar `AIExplainerPort.explain()` para obtener `AIExplanation`, 4)
  persistir el par `(AnomalyRecord, AIExplanation)` vía
  `AnomalyRepositoryPort.save_many()`, 5) construir y persistir el
  `AnalysisRun` resultante.

- **RN-02 (Generación de ids):** `SqlAlchemyAnomalyRepository.save_many` y
  el caso de uso `AnalyzeMeterUseCase` son responsables de generar ids
  nuevos (UUID v4 como string, vía `uuid.uuid4()` de la librería estándar)
  para cada `AnomalyRecord` y `AnalysisRun` — ninguno de esos modelos de
  dominio trae su propio id.

- **RN-03 (Serialización de `affected_variables`):** El repo concreto de
  Anomaly serializa la lista `affected_variables` (`list[str]`) a un string
  separado por comas para guardarla en la columna `String` de `AnomalyORM`,
  y la deserializa de vuelta a `list[str]` al leer (split por coma,
  descartando el caso de string vacío → lista vacía).

- **RN-04 (Contenido de las plantillas de `TemplateExplainerAdapter`):**
  Cada plantilla debe referenciar datos concretos de `anomaly.evidence`, no
  texto genérico:
  - `REAL_ANOMALY`: menciona `variation_pct`, `affected_variables`, y que no
    hay evento operativo conocido que lo explique; recomienda investigar el
    medidor/instalación físicamente.
  - `EXPLAINABLE_ANOMALY`: menciona `variation_pct` y `correlated_event`;
    recomienda validar que el cambio operativo sea el esperado, sin escalar
    como incidente.
  - `FALSE_POSITIVE`: menciona `correlated_event`; recomienda no escalar,
    la desviación es consistente con el evento conocido.
  - `DATA_QUALITY`: menciona `affected_variables` (las eléctricas) y que el
    consumo permanece dentro de lo esperable; recomienda validar/calibrar
    el sensor o instalación de medición.

- **RN-05 (Ejecución síncrona, `AnalysisRun` sin estado intermedio):**
  `AnalyzeMeterUseCase.execute()` corre de forma síncrona dentro del mismo
  request HTTP de `POST /ai/analyze`. `AnalysisRun.status` se asigna
  directamente a `COMPLETED` o `FAILED` al construir el registro — no existe
  un estado `PENDING`/`RUNNING` en este SPEC. `GET /ai/analysis/{id}`
  simplemente consulta el registro ya completo vía
  `AnomalyRunRepositoryPort.get_by_id`.

- **RN-06 (Medidor específico inexistente):** Si `POST /ai/analyze` recibe
  un `meter_id` que no existe (`MeterRepositoryPort.get_by_meter_id`
  retorna `None`), el caso de uso retorna un `AnalysisRun` con
  `status=FAILED`, `anomalies_detected_count=0`, y
  `error_message="Meter '<meter_id>' not found"`. El router traduce esto a
  HTTP 404 (ver CB-04).

- **RN-07 (Análisis de todos los medidores, tolerancia a fallos
  individuales):** Si `meter_id` es `None` (analizar todos), el caso de uso
  itera `meter_repo.get_all()`. Si el análisis de UN medidor individual
  lanza una excepción, esa excepción se captura y el análisis continúa con
  el resto de los medidores — el `AnalysisRun` final es `status=COMPLETED`
  con `anomalies_detected_count` sumando solo los medidores que sí se
  analizaron correctamente. Esto evita que un dato corrupto en un medidor
  tumbe el análisis completo del dashboard. **"Se registra internamente"
  significa acumular una lista de errores por medidor
  (`{meter_id: str, error: str}`) durante la iteración, y — dado que
  `AnalysisRun` (sección 3.1) no tiene un campo para una lista de errores
  parciales, y este SPEC no autoriza agregarle uno — escribir esa lista
  como texto plano en el propio `logging` estándar de Python (`import
  logging; logger.warning(...)`, no `print()`**, que se pierde en stdout sin
  nivel ni contexto estructurado). Esto es una mejora deliberadamente
  acotada: no persiste los errores en la base de datos (eso requeriría
  ampliar `AnalysisRun`, fuera de alcance de este retrabajo), solo los hace
  recuperables vía logs del proceso en vez de invisibles.

- **RN-08 (Derivación de `MeterSummaryResponse.status`):**
  `status="Critical"` si el medidor tiene al menos una anomalía persistida
  con `severity="HIGH"`; `status="Alert"` si tiene al menos una anomalía
  persistida con `severity="MEDIUM"` (y ninguna `HIGH`); `status="OK"` en
  cualquier otro caso (sin anomalías persistidas, o solo `LOW`/
  `FALSE_POSITIVE` de severidad `LOW`).

### 4.2 Casos Borde (CB)

- **CB-01 (Dashboard sin análisis previo):** `GET /dashboard/summary` antes
  de que se haya corrido nunca `POST /ai/analyze` retorna
  `anomalies_detected=0`, `high_priority_count=0`, `average_confidence=null`,
  `last_analysis_at=null` — no lanza error.

- **CB-02 (Medidor sin lecturas):** `GET /meters/{meterId}` para un medidor
  registrado pero sin lecturas (no debería ocurrir con el dataset real, pero
  es un caso borde legítimo) retorna `consumption_kwh=0`,
  `baseline_kwh=null`, `variation_pct=null`, `readings=[]` — HTTP 200, no
  404 (el medidor existe, solo no tiene datos).

- **CB-03 (Medidor inexistente en detalle):** `GET /meters/{meterId}` para
  un `meterId` que no existe en absoluto retorna HTTP 404.

- **CB-04 (Análisis de medidor inexistente vía API):** `POST /ai/analyze`
  con un `meter_id` inexistente retorna HTTP 404 con el `error_message` de
  RN-06 en el body (no HTTP 500).

- **CB-05 (Anomalía inexistente):** `GET /anomalies/{id}` con un id que no
  existe retorna HTTP 404.

- **CB-06 (Filtros de `/meters` y `/anomalies` sin resultados):** Un filtro
  que no matchea ningún registro retorna lista vacía `[]`, HTTP 200 — nunca
  404 para una colección filtrada vacía.

- **CB-07 (Doble corrida de análisis sobre el mismo medidor):** Correr
  `POST /ai/analyze` dos veces seguidas para el mismo medidor genera DOS
  conjuntos de `AnomalyRecord` persistidos (uno por corrida) — a diferencia
  de los repos de SPEC-002, este repo NO es idempotente por diseño (RN-02),
  cada análisis es un evento nuevo con su propio `detected_at`.

---

## 5. Plan de Ejecución Secuencial (Atomic Tasks)

- [x] **Paso 1: Modelo `AnalysisRun`, `PersistedAnomaly`, y puertos nuevos:**
  Crear `anomaly_run.py`, agregar `PersistedAnomaly` a
  `app/domain/models/anomaly.py` (sección 3.1-bis), crear
  `anomaly_repository_port.py`, `anomaly_run_repository_port.py` según
  sección 3.2. Actualizar `app/domain/ports/__init__.py` (agregar también el
  export de `PersistedAnomaly` en `app/domain/models/__init__.py` si ese
  `__init__.py` re-exporta los demás modelos de `anomaly.py` — revisa el
  archivo existente antes de decidir).
- [x] **Paso 2: Modelos ORM y repos concretos de Anomaly/AnalysisRun:**
  Implementar `AnomalyORM`/`AnalysisRunORM` (sección 3.3),
  `SqlAlchemyAnomalyRepository`, `SqlAlchemyAnomalyRunRepository`,
  cumpliendo RN-02, RN-03, CB-07.
- [x] **Paso 3: `TemplateExplainerAdapter`:** Implementar según sección 3.4
  y RN-04 (4 plantillas, una por `AnomalyType`).
- [x] **Paso 4: Casos de uso:** Implementar `AnalyzeMeterUseCase` (sección
  3.5, RN-01, RN-05, RN-06, RN-07) y los 5 casos de uso de solo lectura,
  cumpliendo RN-08 y los CB de la sección 4.2 relevantes a cada uno.
- [x] **Paso 5: Schemas y routers FastAPI:** Implementar `schemas.py` y los
  4 routers según sección 3.6, sin lógica de negocio en los routers.
- [x] **Paso 6: Composition root:** Implementar `app/main.py` — construye el
  engine (reutilizando `create_db_engine`/`create_all_tables` de SPEC-002),
  instancia repos concretos, `TemplateExplainerAdapter`, `AnomalyDetector`,
  los 6 casos de uso, y los registra como dependencias de FastAPI
  (`Depends`) en los routers, que se incluyen en la app vía
  `app.include_router(...)`.
  > **Nota post-implementación:** tras 2 rondas de retrabajo, el composition
  > root quedó con una sesión de SQLAlchemy compartida por request
  > (`build_X_use_case(session: Session = Depends(get_db_session))`), no
  > con repos construidos ad-hoc por `get_engine()` suelto como en la
  > primera entrega. Ver sección 3.7 y 3.8.
- [x] **Paso 7: Tests unitarios de aplicación/adapters:** Tests de
  `AnalyzeMeterUseCase` con repos/detector/explainer **mockeados** (no DB
  real — es unitario) cubriendo RN-01, RN-05, RN-06, RN-07. Tests de
  `TemplateExplainerAdapter` cubriendo las 4 ramas de RN-04.
- [x] **Paso 8: Tests de integración de persistencia:** Tests de
  `SqlAlchemyAnomalyRepository` y `SqlAlchemyAnomalyRunRepository` contra
  SQLite real (temporal), cubriendo RN-02, RN-03, CB-07. Incluye
  `test_shared_session_atomicity` y `test_transaction_rollback_atomicity`
  (sección 3.8) — este último verificado independientemente: se confirmó
  que el engine `sqlite:///:memory:` comparte conexión entre sesiones
  (descartando falso positivo por bases aisladas) antes de aceptar el test.
- [x] **Paso 9: Tests e2e:** Tests con `TestClient` de FastAPI contra la app
  completa (DB de test, no la real del proyecto) cubriendo el flujo
  `POST /ai/analyze` → `GET /anomalies` → `GET /anomalies/{id}` end-to-end,
  y los casos borde CB-01 a CB-06.
- [x] **Paso 10: Validación:** `pytest backend/tests/unit
  backend/tests/integration backend/tests/e2e -v` — 64/64 en verde,
  confirmado en venv aislado independiente. Servidor levantado contra la
  base real sembrada por SPEC-002, `POST /ai/analyze` con `meter_id=null`
  disparado manualmente y `GET /anomalies` leído directamente: M-109
  `REAL_ANOMALY/HIGH`, M-104 `EXPLAINABLE_ANOMALY/MEDIUM`, M-106
  `FALSE_POSITIVE/LOW`, M-112 `DATA_QUALITY/HIGH` — coincide exactamente
  con `ARCHITECTURE.md` §1. Seed corrido dos veces seguidas: conteos
  idénticos (12/4032/4), idempotencia intacta tras el cambio de
  commit→flush.

---

## 6. Verificación y Checklist de Salida (Pipeline de 5 Pasos)

- [x] **1. Validación Arquitectónica:**
  - `app/domain/` sigue sin importar nada de `app/adapters/` ni
    `app/application/` — verificado por grep, sin resultados.
  - `app/application/` depende solo de puertos (`Protocol`), nunca importa
    directamente `SqlAlchemyAnomalyRepository`, `TemplateExplainerAdapter`,
    ni ningún otro adapter concreto — la inyección ocurre en `main.py`.
    Verificado por grep de imports en `app/application/`.
  - Routers FastAPI no contienen lógica de negocio (solo parseo/validación
    de input + llamada a caso de uso + serialización de output).
  - `git diff` coincide únicamente con los archivos autorizados en la
    Sección 1. Los 3 repos de SPEC-002 tocados (`meter_repository.py`,
    `reading_repository.py`, `event_repository.py`) lo fueron bajo la
    autorización excepcional explícita de la sección 3.8 (commit→flush
    únicamente, verificado que ningún otro comportamiento cambió).
- [x] **2. Generación de Tests:**
  - Tests unitarios (casos de uso + `TemplateExplainerAdapter`), de
    integración (repos de Anomaly/AnalysisRun + atomicidad transaccional),
    y e2e (API completa), derivados directamente de RN-01..RN-08 y
    CB-01..CB-07 (64 tests en total, sumando los 46 heredados de
    SPEC-001/SPEC-002 sin modificar su intención original).
- [x] **3. Validación de Cobertura:**
  - `pytest` ejecutado exitosamente (0 errores, 64/64) sobre `tests/unit` +
    `tests/integration` + `tests/e2e` combinados. Cobertura medida con
    `pytest-cov`: 93% total sobre `app/`. Nota honesta: `list_meters.py`
    quedó con 48% de cobertura (el cuerpo de `execute()` no está cubierto
    por un caso con anomalías asociadas en los tests unitarios/integración,
    aunque el endpoint fue verificado funcionalmente contra el servidor
    real) — no bloqueante para este SPEC, pero señalado para reforzar en
    una iteración futura si se retoma esa capa.
- [x] **4. Documentación As-Built:**
  - Docstrings completos (Google style) en cada caso de uso, repositorio,
    adapter, y router.
- [x] **5. Trazabilidad y Estado:**
  - Checklist de este SPEC completado y entrada registrada en
    `specs/TASK_STATUS.md`.
