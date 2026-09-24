# SPEC: SPEC-004 - Adapter Claude (Agentic Loop) para Explicación de Anomalías

> **Instrucciones para el Agente Codificador:**
> 1. No instales dependencias externas, librerías ni paquetes que no estén explícitamente autorizados en la sección 2.
> 2. No agregues campos adicionales, métodos auxiliares públicos ni endpoints fuera de los contratos descritos en la sección 3.
> 3. Implementa únicamente las tareas listadas en la sección 5 en orden secuencial. Si encuentras un bloqueo, detén la ejecución y solicita aclaración.
> 4. Sigue el **Protocolo de Fronteras de STANDARDS.md sección 2** sin excepción: antes de tocar cualquier archivo, cotéjalo contra la sección 1 de este SPEC; antes de escribir cualquier firma, cotéjala contra la sección 3. Estar autorizado a crear/modificar un archivo NO autoriza a desviarte de las firmas/campos/comportamientos exactos definidos en la sección 3. Si algo no encaja, emite `BLOCKED_BY_BOUNDARY: <archivo/firma> — <razón>` y detente.
> 5. Al finalizar, ejecuta `pytest backend/tests/unit backend/tests/integration backend/tests/e2e -v` y confirma que todos los tests pasan antes de marcar el SPEC como completo. **Ningún test de este SPEC llama a la API real de Anthropic** — todos los tests que ejercitan `ClaudeExplainerAdapter` usan un cliente de Anthropic mockeado/fake (ver sección 4, `STANDARDS.md` §5).
> 6. `app/domain/`, todo lo de SPEC-002, y todo lo de SPEC-003 (casos de uso, routers, `main.py`, `TemplateExplainerAdapter`) ya están cerrados y auditados. No los modifiques salvo lo explícitamente autorizado en la sección 1.

---

## 1. Alcance y Fronteras

* **Objetivo:** Implementar `ClaudeExplainerAdapter`, la implementación real
  de `AIExplainerPort` que usa la API de Claude con un agentic loop de tool
  use (consulta eventos operativos reales vía una tool, luego sintetiza
  `reason`/`recommended_action`), con fallback automático al
  `TemplateExplainerAdapter` ya existente (SPEC-003) si la API falla, no hay
  API key configurada, o se agota el tiempo de espera.

* **En Alcance (In-Scope):**
  - `ClaudeExplainerAdapter`: adapter que implementa `AIExplainerPort`,
    usando el SDK oficial de Anthropic (`anthropic` — tool use nativo del
    SDK, no un servidor MCP separado).
  - Una función Python interna, `get_events_tool`, registrada como "tool"
    en el formato que espera la API de Claude (JSON schema), que — cuando
    Claude decide llamarla — consulta `EventRepositoryPort.get_by_meter_id`
    (inyectado en el constructor del adapter) y devuelve los eventos reales
    del medidor en el rango temporal de la anomalía.
  - Fallback automático: si la llamada a la API falla (error de red,
    timeout, respuesta inválida) o `Settings.anthropic_api_key` es `None`,
    el adapter delega internamente al `TemplateExplainerAdapter` ya
    existente — la demo nunca debe romperse por falta de red/credenciales.
  - `Settings.anthropic_api_key` nuevo en `app/config.py` (SPEC-002,
    reabierto solo para este campo — ver sección 1, "Modificar").
  - `app/main.py` (SPEC-003, reabierto): construye `ClaudeExplainerAdapter`
    en vez de `TemplateExplainerAdapter` directamente cuando hay API key
    configurada; sigue usando `TemplateExplainerAdapter` cuando no la hay.

* **Fuera de Alcance (Out-of-Scope / Non-Goals):**
  - Servidor MCP real/separado — se usa tool-use nativo del SDK de
    Anthropic, más simple y sin proceso adicional que mantener para la demo.
  - Streaming de la respuesta de Claude.
  - Cachear o reusar explicaciones entre corridas de análisis — cada
    llamada a `explain()` es independiente.
  - Modificar `AIExplainerPort`, `AIExplanation`, `TemplateExplainerAdapter`,
    o cualquier caso de uso — el contrato del puerto (SPEC-001) ya está
    cerrado y este SPEC solo agrega una implementación alternativa que lo
    satisface igual que `TemplateExplainerAdapter`.
  - Modificar `AnomalyDetector` o cualquier regla de clasificación — Claude
    nunca decide tipo/severidad/confianza, solo redacta texto (regla ya
    establecida en `ARCHITECTURE.md` §4, no se reabre aquí).

* **Archivos Afectados:**
  * **Crear:**
    - `backend/app/adapters/outbound/ai/claude_explainer_adapter.py`
    - `backend/app/adapters/outbound/ai/claude_tools.py` (definición de la
      tool `get_events` en formato JSON schema + la función Python que la
      ejecuta)
    - `backend/tests/unit/adapters/test_claude_explainer_adapter.py`
  * **Modificar:**
    - `backend/app/config.py` — agregar únicamente el campo
      `anthropic_api_key: str | None = None` y
      `claude_model: str = "claude-sonnet-4-6"` a la clase `Settings` ya
      existente. Ningún otro campo/comportamiento de `Settings` cambia.
    - `backend/app/main.py` — reemplazar la función `get_explainer()`
      (o el `build_X_use_case` que la usa, según cómo haya quedado
      estructurado tras SPEC-003) para que construya
      `ClaudeExplainerAdapter` cuando `settings.anthropic_api_key` no es
      `None`, y `TemplateExplainerAdapter` en caso contrario. Ningún otro
      wiring de `main.py` cambia.
    - `backend/requirements.txt` — agregar `anthropic` (ver sección 2).
  * **Prohibido modificar:**
    - `backend/app/domain/**` (todo SPEC-001, cerrado)
    - `backend/app/domain/ports/ai_explainer_port.py` (contrato ya cerrado
      — `AIExplainerPort`/`AIExplanation` no cambian)
    - `backend/app/adapters/outbound/ai/template_explainer_adapter.py`
      (SPEC-003, cerrado — el fallback se REUSA, no se modifica)
    - Todo lo de `backend/app/adapters/outbound/persistence/` (SPEC-002/
      SPEC-003, cerrado)
    - `backend/app/application/**` (SPEC-003, cerrado — ningún caso de uso
      cambia; `AnalyzeMeterUseCase` sigue recibiendo un `AIExplainerPort`
      genérico sin saber qué implementación concreta es)
    - `backend/app/adapters/inbound/**` (SPEC-003, cerrado — ningún router
      ni schema cambia)
    - `readings.csv`, `events.csv`

---

## 2. Entorno y Dependencias Permitidas

* **Runtime / Versión:** Python 3.11+
* **Librerías autorizadas (nueva, se agrega a las ya existentes):**
  - `anthropic>=0.40` (SDK oficial de Anthropic, incluye soporte de tool
    use nativo)
  - Las ya autorizadas en SPEC-001/002/003: `pydantic>=2.0`, `pytest>=7.0`,
    `sqlalchemy>=2.0`, `pydantic-settings>=2.0`, `fastapi>=0.110`,
    `uvicorn[standard]>=0.29`, `httpx>=0.27`
* **Regla estricta:** Prohibido cualquier otro SDK de LLM (`openai`,
  `langchain`, `llama-index`, etc.), cualquier librería de MCP
  (`mcp`, `fastmcp`), o cualquier framework de agentes de terceros. El
  agentic loop se implementa a mano con el SDK de Anthropic directo —
  simple y auditable, sin abstracciones de terceros.

---

## 3. Contratos e Interfaces (Single Source of Truth)

### 3.1 `Settings` — campos nuevos

```python
# backend/app/config.py — SOLO se agregan estos 2 campos a la clase
# Settings ya existente; database_url y model_config no cambian.
class Settings(BaseSettings):
    database_url: str = "sqlite:///./bia_energy.db"
    anthropic_api_key: str | None = None
    claude_model: str = "claude-sonnet-4-6"

    model_config = {"env_prefix": "BIA_"}
```

> `anthropic_api_key` se lee de la variable de entorno `BIA_ANTHROPIC_API_KEY`
> (por el `env_prefix` ya configurado). Si no está seteada, queda `None` —
> ese es exactamente el valor que `main.py` usa para decidir si construir
> `ClaudeExplainerAdapter` o `TemplateExplainerAdapter`.

### 3.2 Tool `get_events` (`claude_tools.py`)

```python
# backend/app/adapters/outbound/ai/claude_tools.py
from app.domain.ports.event_repository_port import EventRepositoryPort

GET_EVENTS_TOOL_SCHEMA: dict = {
    "name": "get_events",
    "description": (
        "Retorna los eventos operativos conocidos de un medidor eléctrico "
        "(cambios operacionales, mantenimientos programados, problemas de "
        "calidad de datos) que puedan explicar una anomalía detectada."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "meter_id": {
                "type": "string",
                "description": "Código del medidor, ej. 'M-109'.",
            },
        },
        "required": ["meter_id"],
    },
}


def execute_get_events_tool(
    event_repo: EventRepositoryPort, meter_id: str
) -> list[dict]:
    """Ejecuta la tool get_events contra el repositorio real de eventos.

    Args:
        event_repo: Puerto de repositorio de eventos, inyectado por el
            adapter que invoca esta función.
        meter_id: Código del medidor a consultar.

    Returns:
        Lista de dicts serializables a JSON (uno por evento), con las
        claves: event_timestamp (ISO string), event_type (str),
        description (str). Lista vacía si el medidor no tiene eventos.
    """
    ...
```

> El schema NO incluye `from_ts`/`to_ts` como en el diseño original de
> `ARCHITECTURE.md` §4.1 (`get_events(meter_id, from_ts, to_ts)`) — se
> simplifica a `get_events(meter_id)` porque `EventRepositoryPort` (SPEC-002,
> cerrado, no se puede modificar) solo expone `get_by_meter_id(meter_id)` y
> `get_all()`, sin filtro de rango temporal. Claude recibe TODOS los
> eventos del medidor y decide cuáles son relevantes por su propio
> `event_timestamp` en la síntesis — es una simplificación deliberada frente
> al diseño original, aceptable porque el dataset tiene como máximo 1 evento
> por medidor "interesante" (ver `events.csv`), así que filtrar por rango no
> aporta valor real en este alcance.

### 3.3 `ClaudeExplainerAdapter`

```python
# backend/app/adapters/outbound/ai/claude_explainer_adapter.py
from anthropic import Anthropic

from app.domain.models.anomaly import AnomalyRecord
from app.domain.ports.ai_explainer_port import AIExplanation, AIExplainerPort
from app.domain.ports.event_repository_port import EventRepositoryPort
from app.adapters.outbound.ai.template_explainer_adapter import TemplateExplainerAdapter


class ClaudeExplainerAdapter(AIExplainerPort):
    """Implementación de AIExplainerPort vía la API de Claude, con un
    agentic loop de 2 pasos (tool call a get_events + síntesis) y fallback
    automático a TemplateExplainerAdapter si la llamada falla.
    """

    def __init__(
        self,
        event_repo: EventRepositoryPort,
        api_key: str,
        model: str,
        fallback: TemplateExplainerAdapter | None = None,
        max_tool_iterations: int = 3,
    ) -> None:
        """Configura el cliente de Anthropic y las dependencias del loop.

        Args:
            event_repo: Puerto de repositorio de eventos, usado por la tool
                get_events cuando Claude decide invocarla.
            api_key: API key de Anthropic.
            model: Identificador del modelo de Claude a usar.
            fallback: Adapter de respaldo si la llamada a la API falla. Si
                no se provee, se instancia un TemplateExplainerAdapter()
                nuevo internamente.
            max_tool_iterations: Máximo de rondas de tool-calling permitidas
                antes de forzar una respuesta final (evita loops infinitos
                si el modelo insiste en llamar tools).
        """
        ...

    def explain(self, anomaly: AnomalyRecord) -> AIExplanation:
        """Genera explicación vía Claude con un agentic loop de tool use.

        Flujo: 1) construye el prompt inicial con los hechos de
        `anomaly.evidence` (nunca con tipo/severidad como si fueran
        decisión del LLM — esos ya están decididos), con la tool
        `get_events` disponible; 2) si Claude pide llamar la tool, la
        ejecuta contra `event_repo` y le devuelve el resultado; 3) repite
        hasta que Claude entregue una respuesta final estructurada (sin más
        tool calls) o se alcance `max_tool_iterations`; 4) parsea la
        respuesta final a `AIExplanation`.

        Si en cualquier punto la llamada a la API lanza una excepción
        (red, timeout, rate limit, respuesta malformada), o si Claude no
        entrega una respuesta parseable como AIExplanation dentro de
        max_tool_iterations, cae al fallback (RN-04) — nunca propaga la
        excepción hacia el caller.

        Args:
            anomaly: Registro de anomalía clasificada por el dominio.

        Returns:
            AIExplanation generada por Claude, o por el fallback si algo
            falló.
        """
        ...
```

---

## 4. Reglas de Negocio y Casos Borde

### 4.1 Reglas de Negocio (RN)

- **RN-01 (Prompt inicial):** El primer mensaje enviado a Claude incluye
  únicamente hechos ya calculados por el dominio — `meter_id`,
  `type`/`severity`/`confidence` (como contexto informativo, no como algo
  que Claude deba decidir), y todos los campos de `anomaly.evidence`
  (`baseline_kwh`, `observed_kwh`, `variation_pct`, `affected_variables`,
  `correlated_event`, `window_start`, `window_end`). El prompt indica
  explícitamente que Claude puede usar la tool `get_events` para consultar
  eventos operativos del medidor si lo considera útil, y que debe responder
  con una explicación (`reason`) y una acción recomendada
  (`recommended_action`) basadas en los datos, nunca reclasificando el tipo
  o severidad ya asignados.

- **RN-02 (Formato de respuesta final):** Claude debe responder en un
  formato parseable a `AIExplanation` (dos campos: `reason`,
  `recommended_action`). Usa tool use también para la respuesta final (una
  segunda tool, p.ej. `submit_explanation(reason: str,
  recommended_action: str)`, que Claude "llama" para estructurar su
  respuesta) — más confiable que parsear texto libre o JSON embebido en
  prosa. Si el modelo nunca llama esa tool de salida dentro de
  `max_tool_iterations`, se activa el fallback (RN-04).

- **RN-03 (Agentic loop, máximo de iteraciones):** El loop de tool-calling
  se limita a `max_tool_iterations` rondas (default 3: suficiente para
  1 llamada a `get_events` + la respuesta final, con margen). Si se agota
  el límite sin obtener una respuesta final parseable, se activa el
  fallback.

- **RN-04 (Fallback determinista, nunca propaga excepciones):**
  `ClaudeExplainerAdapter.explain()` NUNCA lanza una excepción hacia el
  caller. Cualquier fallo (API inalcanzable, timeout, rate limit, respuesta
  sin la tool de salida, excepción de parseo) se captura internamente y
  delega a `self._fallback.explain(anomaly)` (el `TemplateExplainerAdapter`
  ya existente, sin modificarlo). El caller (`AnalyzeMeterUseCase`, ya
  cerrado en SPEC-003) no necesita saber si la explicación vino de Claude o
  del fallback — el contrato `AIExplainerPort` es idéntico en ambos casos.

- **RN-05 (Selección del adapter en `main.py`):** Si
  `settings.anthropic_api_key` es `None` o cadena vacía, `main.py`
  construye `TemplateExplainerAdapter()` directamente (ni siquiera
  instancia `ClaudeExplainerAdapter` — evita cualquier intento de red sin
  credenciales). Si hay una API key configurada, construye
  `ClaudeExplainerAdapter(event_repo=..., api_key=settings.anthropic_api_key,
  model=settings.claude_model)`.

### 4.2 Casos Borde (CB)

- **CB-01 (Sin API key):** Con `BIA_ANTHROPIC_API_KEY` no seteada,
  `main.py` nunca instancia `ClaudeExplainerAdapter` — el sistema completo
  sigue funcionando con `TemplateExplainerAdapter`, sin ningún error
  visible al usuario (comportamiento ya cerrado en SPEC-003, este SPEC no
  lo cambia, solo lo confirma).

- **CB-02 (Medidor sin eventos):** Si Claude llama a `get_events` para un
  medidor sin eventos operativos conocidos, la tool retorna `[]` — Claude
  debe poder seguir generando una explicación coherente (ej. "sin evento
  operativo conocido que lo explique") sin que esto cuente como un error
  del adapter.

- **CB-03 (Timeout/error de red a mitad del loop):** Si la API falla
  DESPUÉS de que Claude ya llamó a `get_events` (o sea, a mitad del loop,
  no en la primera llamada), el fallback se activa igual — no hay un estado
  parcial "explicación a medio generar" que se persista o se muestre.

- **CB-04 (Respuesta de Claude sin campos esperados):** Si Claude "llama"
  la tool de salida (`submit_explanation`) pero con argumentos faltantes o
  de tipo incorrecto (ej. `reason` ausente), el intento de construir
  `AIExplanation` falla la validación de pydantic — se captura como
  cualquier otra excepción y activa el fallback (RN-04), no se relanza.

---

## 5. Plan de Ejecución Secuencial (Atomic Tasks)

- [x] **Paso 1: Configuración:** Agregar `anthropic_api_key` y
  `claude_model` a `Settings` (sección 3.1). Agregar `anthropic` a
  `requirements.txt`.
  > **Nota post-implementación:** la primera entrega dejó `claude_model`
  > con el default `"claude-3-5-sonnet-20240620"` (modelo antiguo) en vez
  > de `"claude-sonnet-4-6"` como especifica esta sección — corregido en
  > auditoría antes de aprobar el SPEC.
- [x] **Paso 2: Tool de eventos:** Implementar `claude_tools.py`
  (`GET_EVENTS_TOOL_SCHEMA`, `execute_get_events_tool`) según sección 3.2.
- [x] **Paso 3: `ClaudeExplainerAdapter`:** Implementar el agentic loop
  completo según sección 3.3, cumpliendo RN-01 a RN-05 y CB-01 a CB-04.
- [x] **Paso 4: Wiring en `main.py`:** Actualizar la construcción del
  explainer según RN-05 — API key presente → `ClaudeExplainerAdapter`; API
  key ausente → `TemplateExplainerAdapter`.
- [x] **Paso 5: Tests unitarios:** Implementar
  `test_claude_explainer_adapter.py` cubriendo RN-01 a RN-05 y CB-01 a
  CB-04, usando un cliente de Anthropic **mockeado/fake** (5 tests: flujo
  normal, fallback por excepción, fallback por argumentos faltantes,
  iteraciones agotadas, y múltiples tool blocks + tool desconocida en la
  misma respuesta). Ningún test llama a la API real de Anthropic.
- [x] **Paso 6: Validación:** `pytest backend/tests/unit
  backend/tests/integration backend/tests/e2e -v` — 69/69 en verde,
  confirmado en venv aislado independiente (incluye los 64 tests
  heredados de SPEC-001/002/003 sin cambios). No había API key real de
  Anthropic disponible para la prueba manual con la IA real — se verificó
  en su lugar CB-01 (sin API key) end-to-end contra el servidor real:
  4 anomalías detectadas correctamente vía `TemplateExplainerAdapter`, sin
  ningún intento de red a Anthropic.

---

## 6. Verificación y Checklist de Salida (Pipeline de 5 Pasos)

- [x] **1. Validación Arquitectónica:**
  - `app/domain/` sigue sin importar nada de `app/adapters/` ni
    `app/application/` — verificado por grep.
  - `ClaudeExplainerAdapter` implementa `AIExplainerPort` sin alterar su
    contrato — es intercambiable con `TemplateExplainerAdapter` desde la
    perspectiva de `AnalyzeMeterUseCase` (que no cambia).
  - `git diff` coincide únicamente con los archivos autorizados en la
    Sección 1. Nada de `app/domain/`, `app/application/`,
    `app/adapters/inbound/`, `app/adapters/outbound/persistence/`, ni
    `template_explainer_adapter.py` aparece modificado.
- [x] **2. Generación de Tests:**
  - Tests unitarios derivados directamente de RN-01..RN-05 y CB-01..CB-04,
    usando un cliente de Anthropic mockeado — nunca la API real.
- [x] **3. Validación de Cobertura:**
  - `pytest` ejecutado exitosamente (0 errores, 69/69) sobre `tests/unit` +
    `tests/integration` + `tests/e2e` combinados. Cobertura medida con
    `pytest-cov`: 93% total; `claude_explainer_adapter.py` 97%,
    `claude_tools.py` 100%.
- [x] **4. Documentación As-Built:**
  - Docstrings completos (Google style) en `ClaudeExplainerAdapter`,
    `execute_get_events_tool`, y los campos nuevos de `Settings`.
- [x] **5. Trazabilidad y Estado:**
  - Checklist de este SPEC completado y entrada registrada en
    `specs/TASK_STATUS.md`.
