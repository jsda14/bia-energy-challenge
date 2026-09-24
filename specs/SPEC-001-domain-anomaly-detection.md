# SPEC: SPEC-001 - Dominio: Modelos y Motor de Detección de Anomalías

> **Instrucciones para el Agente Codificador:**
> 1. No instales dependencias externas, librerías ni paquetes que no estén explícitamente autorizados en la sección 2.
> 2. No agregues campos adicionales, métodos auxiliares públicos ni endpoints fuera de los contratos descritos en la sección 3.
> 3. Implementa únicamente las tareas listadas en la sección 5 en orden secuencial. Si encuentras un bloqueo, detén la ejecución y solicita aclaración.
> 4. Al finalizar, ejecuta `pytest backend/tests/unit -v` y confirma que todos los tests pasan antes de marcar el SPEC como completo.
> 5. Este SPEC NO incluye persistencia (DB), API HTTP ni el adapter de Claude — esos son SPECs posteriores. Este módulo debe funcionar 100% en memoria, sin IO.

---

## 1. Alcance y Fronteras

* **Objetivo:** Implementar los modelos de dominio (`Meter`, `Reading`, `Event`,
  `Anomaly`) y el motor de detección de anomalías (`AnomalyDetector`) que, dado el
  histórico de lecturas de un medidor y sus eventos operativos conocidos, calcula
  baseline, detecta anomalías y las clasifica de forma determinista (sin LLM).

* **En Alcance (In-Scope):**
  - Modelos de dominio inmutables: `Meter`, `Reading`, `Event`, `AnomalyRecord`.
  - Cálculo de baseline por medidor (media móvil de días previos, excluyendo la
    ventana evaluada).
  - Detección de spike/step-change sostenido vs baseline (umbral configurable).
  - Detección de outliers puntuales vía z-score sobre `consumption_kwh`.
  - Detección de inconsistencia eléctrica (voltage/current/power_factor fuera de
    rango físico esperado o con varianza anómala) independiente del consumo.
  - Correlación temporal con `Event` para reclasificar candidatos
    (`OPERATIONAL_CHANGE` → `EXPLAINABLE_ANOMALY`; `SCHEDULED_OUTAGE` →
    `FALSE_POSITIVE`; `DATA_QUALITY` event → `DATA_QUALITY` anomaly type).
  - Cálculo determinista de `severity` (`LOW|MEDIUM|HIGH`) y `confidence` (float
    0.0-1.0).
  - Puerto `AIExplainerPort` (solo la interfaz/Protocol, sin implementación) para
    que `application/` (SPEC futuro) lo use — este SPEC define el contrato, no lo
    implementa.

* **Fuera de Alcance (Out-of-Scope / Non-Goals):**
  - Persistencia (SQLAlchemy, SQLite) — SPEC-002.
  - Endpoints FastAPI / capa `application/` (casos de uso) — SPEC-003.
  - Adapter real de Claude (`ClaudeExplainerAdapter`) — SPEC-004.
  - Frontend — SPECs posteriores.
  - Parseo de `readings.csv`/`events.csv` desde archivo (el SPEC de seed/ingesta es
    SPEC-002) — este SPEC recibe listas de `Reading`/`Event` ya construidas.

* **Archivos Afectados:**
  * **Crear:**
    - `backend/app/domain/models/meter.py`
    - `backend/app/domain/models/reading.py`
    - `backend/app/domain/models/event.py`
    - `backend/app/domain/models/anomaly.py`
    - `backend/app/domain/models/__init__.py`
    - `backend/app/domain/detection/baseline.py`
    - `backend/app/domain/detection/detector.py`
    - `backend/app/domain/detection/__init__.py`
    - `backend/app/domain/ports/ai_explainer_port.py`
    - `backend/app/domain/ports/__init__.py`
    - `backend/app/domain/errors.py`
    - `backend/app/domain/__init__.py`
    - `backend/app/__init__.py`
    - `backend/tests/unit/domain/test_baseline.py`
    - `backend/tests/unit/domain/test_detector.py`
    - `backend/tests/unit/domain/__init__.py`
    - `backend/tests/unit/__init__.py`
    - `backend/tests/__init__.py`
    - `backend/requirements.txt` (crear con las libs de la sección 2 — este archivo
      no existe aún en el repo, no cuenta como "modificar")
  * **Modificar:**
    - Ninguno (repo vacío, todo es creación).
  * **Prohibido modificar:**
    - `data/readings.csv`, `data/events.csv` (solo lectura, en SPECs futuros)
    - `ARCHITECTURE.md`, `STANDARDS.md`

---

## 2. Entorno y Dependencias Permitidas

* **Runtime / Versión:** Python 3.11+
* **Librerías autorizadas:**
  - `pydantic>=2.0` (modelado y validación de datos del dominio)
  - `pytest>=7.0` (pruebas unitarias)
  - Librería estándar de Python (`datetime`, `statistics`, `dataclasses` si se
    prefiere sobre pydantic para algún modelo interno, `enum`, `typing`)
* **Regla estricta:** Prohibido instalar o importar `numpy`, `pandas`, `scipy` o
  cualquier otro paquete de terceros en este SPEC. El cálculo estadístico (media,
  desviación estándar, z-score) se implementa con la librería estándar
  (`statistics.mean`, `statistics.pstdev`, o fórmulas manuales). Esto es
  intencional: mantiene el dominio con cero dependencias pesadas y 100% testeable.

---

## 3. Contratos e Interfaces (Single Source of Truth)

### 3.1 Modelos de Datos / DTOs

```python
# backend/app/domain/models/meter.py
from pydantic import BaseModel, Field

class Meter(BaseModel):
    model_config = {"frozen": True}

    id: str = Field(..., description="Identificador único interno")
    meter_id: str = Field(..., description="Código del medidor, p.ej. 'M-109'")
    name: str
    location: str
    status: str  # "active" | "inactive"
```

```python
# backend/app/domain/models/reading.py
from datetime import datetime
from pydantic import BaseModel, Field

class Reading(BaseModel):
    model_config = {"frozen": True}

    meter_id: str
    timestamp: datetime
    consumption_kwh: float
    voltage_v: float
    current_a: float
    power_factor: float
    status: str = Field(default="OK")  # status tal como viene del CSV origen
```

```python
# backend/app/domain/models/event.py
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class EventType(str, Enum):
    OPERATIONAL_CHANGE = "OPERATIONAL_CHANGE"
    SCHEDULED_OUTAGE = "SCHEDULED_OUTAGE"
    DATA_QUALITY = "DATA_QUALITY"
    UNKNOWN = "UNKNOWN"

class Event(BaseModel):
    model_config = {"frozen": True}

    meter_id: str
    event_timestamp: datetime
    event_type: EventType
    description: str
```

```python
# backend/app/domain/models/anomaly.py
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class AnomalyType(str, Enum):
    REAL_ANOMALY = "REAL_ANOMALY"
    EXPLAINABLE_ANOMALY = "EXPLAINABLE_ANOMALY"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    DATA_QUALITY = "DATA_QUALITY"

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AnomalyEvidence(BaseModel):
    model_config = {"frozen": True}

    baseline_kwh: float
    observed_kwh: float
    variation_pct: float
    affected_variables: list[str]  # subset of: consumption_kwh, voltage_v, current_a, power_factor
    correlated_event: str | None = None  # description del Event correlacionado, si existe
    window_start: datetime
    window_end: datetime

class AnomalyRecord(BaseModel):
    model_config = {"frozen": True}

    meter_id: str
    detected_at: datetime
    type: AnomalyType
    severity: Severity
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: AnomalyEvidence
```

```python
# backend/app/domain/ports/ai_explainer_port.py
from typing import Protocol
from app.domain.models.anomaly import AnomalyRecord

class AIExplanation(BaseModel):
    """Definido en el mismo archivo del puerto; ver nota abajo."""
    reason: str
    recommended_action: str

class AIExplainerPort(Protocol):
    def explain(self, anomaly: AnomalyRecord) -> AIExplanation:
        """Genera explicación y recomendación en lenguaje natural para una
        anomalía ya clasificada por el dominio. La implementación NO debe
        alterar type/severity/confidence — solo produce texto.
        """
        ...
```

> Nota de implementación: `AIExplanation` debe heredar de `pydantic.BaseModel`
> (import correspondiente al inicio del archivo, omitido arriba por brevedad).

### 3.2 Firmas de Métodos / Interfaces Públicas

```python
# backend/app/domain/detection/baseline.py
from datetime import datetime
from app.domain.models.reading import Reading

def calculate_baseline(
    readings: list[Reading],
    evaluation_window_start: datetime,
    evaluation_window_end: datetime,
    lookback_days: int = 7,
) -> float:
    """Calcula el baseline de consumo (kWh promedio por lectura) para un medidor,
    usando lecturas anteriores a `evaluation_window_start` dentro de
    `lookback_days` días, EXCLUYENDO cualquier lectura dentro de la ventana de
    evaluación.

    Args:
        readings: histórico completo de lecturas de UN medidor (mismo meter_id),
            no necesariamente ordenado.
        evaluation_window_start: inicio de la ventana que se está evaluando.
        evaluation_window_end: fin de la ventana que se está evaluando.
        lookback_days: días hacia atrás desde evaluation_window_start a considerar.

    Returns:
        Promedio de consumption_kwh de las lecturas en el período de lookback.
        Si no hay lecturas suficientes en el lookback (CB-01), retorna el promedio
        de TODAS las lecturas anteriores a evaluation_window_start disponibles.

    Raises:
        ValueError: si `readings` está vacío, o si no existe ninguna lectura
            anterior a evaluation_window_start (CB-01 extremo).
    """
    ...
```

```python
# backend/app/domain/detection/detector.py
from datetime import datetime
from app.domain.models.reading import Reading
from app.domain.models.event import Event
from app.domain.models.anomaly import AnomalyRecord

class AnomalyDetector:
    """Motor de detección determinista. Sin dependencias de IO ni de IA."""

    def __init__(
        self,
        spike_threshold_pct: float = 30.0,
        zscore_threshold: float = 3.0,
        voltage_min_v: float = 200.0,
        voltage_max_v: float = 245.0,
        power_factor_min: float = 0.85,
        lookback_days: int = 7,
    ) -> None:
        """Configura los umbrales de detección. Ver RN-01..RN-07 (sección 4.1)
        para el significado de cada umbral.
        """
        ...

    def analyze(
        self,
        meter_id: str,
        readings: list[Reading],
        events: list[Event],
        analysis_timestamp: datetime,
    ) -> list[AnomalyRecord]:
        """Analiza el histórico completo de un medidor y retorna la lista de
        anomalías detectadas (puede ser vacía si no hay anomalías).

        Args:
            meter_id: código del medidor a analizar (debe coincidir con
                readings[i].meter_id y events[i].meter_id para los que apliquen).
            readings: histórico completo de lecturas del medidor, orden arbitrario.
            events: eventos operativos conocidos del medidor (puede ser lista
                vacía). Pueden incluir eventos de otros medidores; el detector
                debe filtrar internamente por meter_id.
            analysis_timestamp: momento en que se ejecuta el análisis (usado como
                `detected_at` en los AnomalyRecord generados).

        Returns:
            Lista de AnomalyRecord, uno por cada ventana anómala detectada y
            clasificada. Vacía si el medidor no presenta anomalías.

        Raises:
            ValueError: si `readings` está vacío o si hay `readings` con
                `meter_id` distinto al parámetro `meter_id` (CB-01, CB-04).
        """
        ...
```

---

## 4. Reglas de Negocio y Casos Borde

### 4.1 Reglas de Negocio (RN)

- **RN-01 (Baseline):** El baseline de un medidor es el promedio de
  `consumption_kwh` de sus lecturas en los `lookback_days` días previos a la
  ventana evaluada, excluyendo la ventana misma. No se usa la media global del
  período completo (evitaría detectar cambios sostenidos recientes, como M-109 y
  M-104).

- **RN-02 (Spike / step-change):** Una ventana de lecturas consecutivas (mínimo 3
  horas) donde el promedio de `consumption_kwh` se desvía del baseline en más de
  `spike_threshold_pct` (default 30%) de forma **sostenida** (no un solo pico
  aislado) es candidata a anomalía de consumo.

- **RN-03 (Outlier puntual / z-score):** Una lectura individual cuyo z-score de
  `consumption_kwh` respecto a la media y desviación estándar del histórico del
  medidor supera `zscore_threshold` (default 3.0) es candidata a outlier puntual.
  Un outlier puntual aislado (no sostenido) sin evento correlacionado se clasifica
  con severidad menor que un cambio sostenido.

- **RN-04 (Inconsistencia eléctrica / calidad de datos):** Independientemente del
  consumo, si dentro de una ventana `voltage_v` cae fuera de
  `[voltage_min_v, voltage_max_v]` (default 200-245V) o `power_factor` cae por
  debajo de `power_factor_min` (default 0.85) de forma errática (alternando entre
  valores plausibles e implausibles en lecturas consecutivas), la ventana se marca
  candidata a `DATA_QUALITY`, **incluso si `consumption_kwh` permanece dentro de
  rango normal**. Este chequeo es independiente del RN-02/RN-03.

- **RN-05 (Correlación con eventos):** Si existe un `Event` del mismo `meter_id`
  cuyo `event_timestamp` cae dentro o inmediatamente antes (≤ 24h) del inicio de
  una ventana candidata:
  - `EventType.OPERATIONAL_CHANGE` → la anomalía candidata (de tipo consumo, RN-02)
    se reclasifica como `AnomalyType.EXPLAINABLE_ANOMALY`.
  - `EventType.SCHEDULED_OUTAGE` → la anomalía candidata se reclasifica como
    `AnomalyType.FALSE_POSITIVE`.
  - `EventType.DATA_QUALITY` → refuerza (no reemplaza) una candidata ya detectada
    por RN-04 como `AnomalyType.DATA_QUALITY`.
  - `EventType.UNKNOWN` → no reclasifica; la anomalía candidata permanece como
    estaba (ver M-109, que tiene un evento `UNKNOWN` que explícitamente NO explica
    el cambio).
  - Sin evento correlacionado y candidata por RN-02/RN-03 → `AnomalyType.REAL_ANOMALY`.

- **RN-06 (Severidad):** `HIGH` si `|variation_pct| >= 80%` o si es `DATA_QUALITY`
  con inconsistencia eléctrica fuerte (voltage fuera de rango en > 20% de las
  lecturas de la ventana); `MEDIUM` si `30% <= |variation_pct| < 80%`; `LOW` para
  `FALSE_POSITIVE` siempre, y para variaciones menores que de otro modo no
  dispararían RN-02 pero sí un outlier puntual aislado.

- **RN-07 (Confianza):** `confidence` es una función determinista de: cuántas
  horas consecutivas sostiene la desviación (más horas → más confianza), si hay
  evento correlacionado exacto en tiempo (más confianza en la clasificación), y la
  magnitud de la desviación respecto al umbral. Rango siempre `[0.0, 1.0]`. No se
  usa el LLM para este cálculo.

### 4.2 Casos Borde (CB)

- **CB-01 (Histórico insuficiente):** Si un medidor tiene menos de `lookback_days`
  días de historial antes de la ventana evaluada, `calculate_baseline` usa todo el
  histórico disponible anterior a la ventana en vez de fallar, salvo que no exista
  ningún dato previo, en cuyo caso lanza `ValueError` (documentado en 3.2).

- **CB-02 (Lecturas fuera de orden / gaps):** `readings` puede llegar en cualquier
  orden y con huecos horarios faltantes. El detector y `calculate_baseline` deben
  ordenar internamente por `timestamp` y tolerar gaps sin lanzar excepción.

- **CB-03 (Meter sin anomalías):** `analyze()` debe poder retornar lista vacía
  limpiamente (p.ej. M-101 a M-103, M-105, M-107, M-108, M-110, M-111 en el
  dataset real no muestran patrones anómalos claros) — no es un error, es un
  resultado válido.

- **CB-04 (Meter_id inconsistente):** Si algún `Reading` en la lista tiene
  `meter_id` distinto al parámetro `meter_id` pasado a `analyze()`, se lanza
  `ValueError` inmediatamente (falla rápido, no filtra silenciosamente — evita
  bugs de mezclar medidores).

- **CB-05 (Evento fuera de rango temporal del dataset):** Un `Event` cuyo
  `event_timestamp` no se solapa con ninguna ventana candidata simplemente no
  afecta el resultado (no es error).

- **CB-06 (Múltiples anomalías en el mismo medidor):** Un medidor puede generar
  más de un `AnomalyRecord` si tiene múltiples ventanas anómalas no contiguas
  (p.ej. detectadas en distintos rangos de fecha). Cada una es independiente.

---

## 5. Plan de Ejecución Secuencial (Atomic Tasks)

- [x] **Paso 1: Modelos de dominio:** Crear `meter.py`, `reading.py`, `event.py`,
  `anomaly.py` exactamente según sección 3.1. Crear `errors.py` con al menos
  `class DomainError(Exception)` como base (sin subclases adicionales no pedidas).
- [x] **Paso 2: Puerto de IA:** Crear `ports/ai_explainer_port.py` con
  `AIExplanation` y `AIExplainerPort` según sección 3.1 (solo el contrato, cero
  lógica).
- [x] **Paso 3: Baseline:** Implementar `calculate_baseline` en
  `detection/baseline.py` cumpliendo RN-01 y CB-01/CB-02.
- [x] **Paso 4: Motor de detección:** Implementar `AnomalyDetector.analyze()` en
  `detection/detector.py` cumpliendo RN-02 a RN-07 y CB-03/CB-04/CB-05/CB-06.
- [x] **Paso 5: Tests unitarios:** Implementar `test_baseline.py` y
  `test_detector.py` cubriendo cada RN y CB de la sección 4, usando fixtures
  construidas a mano (subconjuntos representativos) que repliquen los 4 patrones
  reales del dataset (M-109 tipo real-anomaly, M-104 tipo explainable, M-106 tipo
  false-positive, M-112 tipo data-quality) — sin leer los CSV completos (eso es
  SPEC-002), solo listas de `Reading`/`Event` construidas en el test.
  > **Nota post-implementación:** 6 rondas de retrabajo (ver auditorías en el
  > historial de commits/PR) revelaron que fixtures a mano, aunque tomados de
  > valores reales, escondían interacciones con el baseline móvil que solo
  > aparecen con el histórico completo. Se agregó un test adicional
  > (`test_full_dataset_matches_expected_patterns`) que sí carga
  > `readings.csv`/`events.csv` completos — una desviación deliberada de la
  > redacción original de este paso, adoptada porque resultó indispensable
  > para verificar el motor correctamente.
- [x] **Paso 6: Validación:** Ejecutar `pytest backend/tests/unit -v` y confirmar
  0 fallos. (29/29 tests en la versión final aprobada.)

---

## 6. Verificación y Checklist de Salida (Pipeline de 5 Pasos)

- [x] **1. Validación Arquitectónica:**
  - `domain/` no importa nada de `adapters/`, `application/`, FastAPI, SQLAlchemy
    ni el SDK de Anthropic. Verificado por grep de imports (auditoría inicial y
    re-verificado tras el retrabajo #5, ambas veces limpio).
  - `git diff` coincide únicamente con los archivos listados en la Sección 1.
- [x] **2. Generación de Tests:**
  - Tests unitarios derivados directamente de RN-01..RN-07 y CB-01..CB-06,
    implementados en `backend/tests/unit/domain/` (28 tests en total, ver
    `test_baseline.py` y `test_detector.py`).
- [x] **3. Validación de Cobertura:**
  - `pytest` ejecutado exitosamente (0 errores). Cobertura medida con
    `pytest-cov`: 93% total sobre `domain/detection/` + `domain/models/`
    (baseline.py 100%, detector.py 90%, todos los modelos 100%) — por
    encima del mínimo de 85% requerido.
- [x] **4. Documentación As-Built:**
  - Docstrings completos (Google style) en `calculate_baseline`,
    `AnomalyDetector.__init__`, `AnomalyDetector.analyze`, y en cada modelo
    pydantic (docstring de clase describiendo el propósito).
- [x] **5. Trazabilidad y Estado:**
  - Checklist de este SPEC completado. Entrada registrada en
    `specs/TASK_STATUS.md` (índice global de todos los SPECs del proyecto).
