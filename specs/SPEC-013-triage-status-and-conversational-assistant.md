# SPEC-013 — Estado de Triage (Atendida/Descartada) y Asistente Conversacional

**Estado:** 🟡 Propuesta, pendiente de aprobación.

## 0. Contexto y motivación

Este SPEC cubre dos capacidades que extienden el flujo de gestión de
anomalías más allá del alcance mínimo definido por el PDF del challenge
(SPEC-001 a SPEC-012): un estado de triage por anomalía (Atendida/
Descartada) y un asistente conversacional que permite consultar y accionar
sobre los datos ya existentes en lenguaje natural. Ambas se tratan como una
extensión explícitamente separada del MVP core, no como requisitos del
flujo mínimo.

**No es una extensión del motor de detección ni de las reglas de negocio
RN-01..RN-06 (SPEC-001, cerradas).** Es una capa de gestión de triage sobre
anomalías ya detectadas, más un canal de consulta/acción conversacional sobre
datos y casos de uso ya existentes.

## 1. Alcance

### 1.1 Backend — Crear

- `app/domain/models/anomaly.py`: agregar el campo `triage_status: str = "NEW"`
  en `PersistedAnomaly` — **`str`, no `Enum`**, siguiendo el precedente real ya
  establecido por `explanation_source` (también `str`, no `Enum`/`Literal`, ver
  `anomaly.py:110`); introducir un `Enum` aquí sería inconsistente con ese
  precedente sin ninguna razón de dominio nueva que lo justifique. Los 3
  valores válidos (`"NEW"`, `"ACKNOWLEDGED"`, `"DISMISSED"`) se documentan en
  el docstring del campo, igual que ya se documenta `explanation_source`. La
  validación de que solo esos 3 valores son aceptados vive en el borde HTTP
  (ver más abajo), no en el modelo de dominio.
- `app/domain/ports/anomaly_repository_port.py`: agregar
  `update_triage_status(anomaly_id: str, triage_status: str) -> bool` (mismo
  contrato de retorno que `update_explanation`: `True` si existía y se
  actualizó, `False` si no).
- `app/adapters/outbound/persistence/anomaly_repository.py`: columna
  `triage_status` en `AnomalyORM` (default `"NEW"`, sin migración necesaria en
  SQLite — mismo criterio ya usado para `explanation_source` en SPEC-010).
  Implementar `update_triage_status`.
- `app/application/update_anomaly_triage_status.py` (nuevo, un solo método
  `execute(anomaly_id: str, status: TriageStatus) -> AnomalyDetailDTO | None`):
  valida que el `anomaly_id` exista, actualiza, retorna el DTO completo
  actualizado (o `None` si no existe — mismo patrón que
  `RegenerateExplanationUseCase`).
- `app/adapters/inbound/api/anomalies_router.py`:
  `PATCH /anomalies/{anomaly_id}/triage-status` — body
  `{"status": Literal["NEW", "ACKNOWLEDGED", "DISMISSED"]}` (el `UpdateTriageStatusRequest`
  en `schemas.py` tipa `status` como `Literal[...]`, no `str` — Pydantic
  rechaza automáticamente cualquier otro valor con 422; es el único punto del
  sistema donde se valida el conjunto cerrado de 3 estados, ya que el dominio
  y la persistencia usan `str` sin restricción, ver 1.1 arriba), responde
  `AnomalyDetailResponse` actualizado o 404. Reversible en cualquier dirección
  entre esos 3 estados (sin restricción de transición) — no hay autenticación
  en el MVP (confirmado desde SPEC-003), así que no existe noción de "quién"
  lo cambió; agregar una máquina de estados con transiciones restringidas
  sería una regla de negocio inventada sin ningún requisito real que la
  sustente.
- `app/adapters/inbound/api/schemas.py`: `AnomalyDetailResponse` y
  `AnomalySummaryResponse` ganan `triage_status: str` (mismo criterio de
  tolerancia ya usado para `explanation_source`: `z.string()`/`str`, no enum
  estricto, para no romper si el dominio agrega un estado nuevo en el futuro).
- `app/application/dtos.py`: `AnomalyDetailDTO`/`AnomalySummaryDTO` ganan
  `triage_status: str`.
- `app/application/list_anomalies.py` / `get_anomaly_detail.py`: propagar el
  campo desde `PersistedAnomaly` sin más lógica.

**Explícitamente fuera de alcance (decisión confirmada con el usuario):**
`GetDashboardSummaryUseCase` (`anomalies_detected`, `high_priority_count`,
`average_confidence`) **no** se toca — sigue contando todas las anomalías
igual que hoy, sin excluir las `DISMISSED`. Es una pieza ya cerrada y
auditada desde SPEC-009; excluir estados del conteo es una decisión de
producto distinta que no se pidió y que ampliaría el alcance de este SPEC
sin necesidad.

### 1.2 Backend — Asistente conversacional

**Mecanismo (decisión explícita, ver sección 0):** mismo patrón de agentic
loop tool-use nativo que `ClaudeExplainerAdapter` (SPEC-004) — **nunca** SQL
libre ni acceso directo a la capa de persistencia vía MCP. Las tools que
Claude puede invocar llaman a los mismos `Ports`/casos de uso ya existentes y
auditados, preservando la arquitectura hexagonal intacta.

- `app/adapters/outbound/ai/assistant_tools.py` (nuevo): define el schema de
  tools disponibles para el asistente:
  - `get_anomalies(severity: str | None, meter_id: str | None)` → lectura,
    llama a `ListAnomaliesUseCase` (ya existe).
  - `get_meter_detail(meter_id: str)` → lectura, llama a
    `GetMeterDetailUseCase` (ya existe).
  - `get_dashboard_summary()` → lectura, llama a
    `GetDashboardSummaryUseCase` (ya existe).
  - `run_analysis(meter_id: str | None)` → **acción con side-effect**, llama a
    `AnalyzeMeterUseCase`/`AnalyzeAllMetersUseCase` (ya existen). Requiere
    confirmación explícita del usuario en el frontend antes de ejecutarse
    (ver 1.4) — el asistente nunca ejecuta esta tool sin que el usuario haya
    confirmado en la UI primero.
  - `set_triage_status(anomaly_id: str, status: str)` → **acción con
    side-effect**, llama a `UpdateAnomalyTriageStatusUseCase` (nuevo, 1.1).
    Mismo requisito de confirmación explícita.
- `app/domain/ports/assistant_port.py` (nuevo): `Protocol` con
  `ask(conversation: list[dict], pending_confirmation: dict | None) -> AssistantResponseDTO`.
  El contrato distingue explícitamente una respuesta de texto normal de una
  respuesta que requiere confirmación de una acción (`AssistantResponseDTO`
  con `text: str`, `pending_action: PendingActionDTO | None` — si
  `pending_action` no es `None`, el frontend debe mostrar un diálogo de
  confirmación antes de reenviar la conversación con
  `pending_confirmation={"confirmed": true/false}`).

  **Formato de `conversation` y recuperación de la acción pendiente (backend
  100% stateless, sin caché de sesión):** cada elemento de `conversation` es
  el mensaje crudo tal como lo entrega/consume el SDK de `anthropic`
  (`{"role": "user" | "assistant", "content": str | list[dict]}` — `content`
  puede ser un array de bloques `text`/`tool_use`/`tool_result`, igual que ya
  usa `ClaudeExplainerAdapter` en `claude_explainer_adapter.py:69`
  `messages.append({"role": "assistant", "content": response.content})`).
  Cuando la respuesta trae `pending_action`, el backend agrega a la
  respuesta también el mensaje `assistant` crudo que contiene el bloque
  `tool_use` original (mismo objeto que devolvió Anthropic, serializado tal
  cual) para que el frontend lo guarde en su historial en memoria sin
  transformarlo. Al confirmar/cancelar, el frontend reenvía `conversation`
  completo (incluyendo ese mensaje `assistant` con el `tool_use`) más
  `pending_confirmation`; el backend simplemente vuelve a llamar a Claude con
  esa conversación — nunca reconstruye un bloque `tool_use` a mano ni
  necesita recordar nada entre requests.
- `app/adapters/outbound/ai/claude_assistant_adapter.py` (nuevo): implementa
  `AssistantPort`. Reutiliza el mismo cliente `anthropic.Anthropic` y el mismo
  criterio de manejo de errores de `ClaudeExplainerAdapter` (cualquier fallo
  de red/timeout/validación responde con un mensaje de error genérico en
  español, nunca una excepción sin capturar). **Sin fallback a plantilla** —
  a diferencia de la explicación de anomalías, un asistente conversacional no
  tiene un fallback determinista sensato; si Claude no está disponible, el
  asistente informa el error al usuario en vez de simular una respuesta.
  Límite de iteraciones del loop: `MAX_ITERATIONS = 5` (más alto que las 3 de
  `ClaudeExplainerAdapter` porque una pregunta de triage puede necesitar
  encadenar más de una tool de lectura antes de responder, ej. "¿cuál medidor
  tiene más anomalías críticas?" → `get_anomalies` → agregación en la
  respuesta de texto).
- `app/application/ask_assistant.py` (nuevo caso de uso): orquesta la llamada
  a `AssistantPort`, sin lógica de negocio propia — es una capa delgada que
  solo adapta el DTO de entrada/salida, mismo criterio que
  `RegenerateExplanationUseCase`.
- `app/adapters/inbound/api/assistant_router.py` (nuevo):
  `POST /assistant/ask` — body
  `{"conversation": [{"role": "user"|"assistant", "content": str}], "pending_confirmation": {"confirmed": bool} | null}`,
  responde `{"text": str, "pending_action": {"tool": str, "description": str} | null}`.
  Sin persistencia de historial de conversación en el backend — el frontend
  mantiene el array `conversation` completo en memoria y lo reenvía en cada
  request (mismo criterio de simplicidad que el resto del MVP: sin sesiones,
  sin autenticación).

### 1.3 Frontend — Estado de triage

- `frontend/src/domain/types.ts`: `AnomalySummary`/`AnomalyDetail` ganan
  `triage_status: string`.
- `frontend/src/api/schemas.ts`: mismo campo en ambos schemas Zod.
- `frontend/src/components/ui/TriageStatusBadge.tsx` (nuevo): mismo patrón
  ya establecido por `SourceBadge`/`Badge` — mapea `"NEW"` → "Nueva" (tono
  neutral), `"ACKNOWLEDGED"` → "Atendida" (tono primary/pulse), `"DISMISSED"`
  → "Descartada" (tono neutral apagado), cualquier valor no reconocido cae a
  "Nueva" (mismo criterio de fallback silencioso que
  `severityToColorToken`).
- `frontend/src/api/queries/useUpdateTriageStatus.ts` (nuevo): mutation
  `PATCH /anomalies/{id}/triage-status`, invalida la query de
  `useAnomalyDetail`/`useAnomalies` al completarse (mismo patrón de
  invalidación que `useRegenerateExplanation`).
- `frontend/src/pages/AnomalyDetailPage.tsx`: agrega dos botones
  ("Marcar como Atendida" / "Descartar") junto al `RunAnalysisButton`
  existente — visibles siempre (acción reversible, sin restricción de
  transición según sección 1.1), deshabilitados mientras la mutation está en
  curso.
- `frontend/src/components/feature/AnomaliesTable.tsx` / `TriageList.tsx`:
  agregan `TriageStatusBadge` como columna/indicador adicional.
- `frontend/src/components/feature/AnomaliesFilterBar.tsx`: agrega filtro
  por `triage_status` (mismo patrón client-side ya usado para
  `status`/`anomaly_severity` desde SPEC-006), con "Todas" como default
  (nunca oculta `DISMISSED` por defecto — sería sorprendente que una
  anomalía "desaparezca" sin que el usuario lo pidiera explícitamente).

### 1.4 Frontend — Asistente conversacional

- `frontend/src/components/feature/AssistantPanel.tsx` (nuevo): panel
  flotante (botón fijo esquina inferior derecha, mismo z-index/patrón de
  overlay que `MobileNav`) con historial de conversación en memoria de
  componente (`useState`, sin persistencia — se pierde al recargar,
  consistente con el backend sin estado de sesión).
- `frontend/src/api/queries/useAssistant.ts` (nuevo): mutation
  `POST /assistant/ask`.
- **Diálogo de confirmación de acciones:** cuando la respuesta trae
  `pending_action`, el panel muestra la descripción de la acción
  (`pending_action.description`, texto ya en español generado por el
  backend, ej. "¿Confirmas ejecutar el análisis para todos los medidores?")
  con botones "Confirmar"/"Cancelar" — nunca se reenvía
  `pending_confirmation: {confirmed: true}` sin un click explícito del
  usuario en el panel. Este es el control de seguridad central de la
  función: el modelo puede *proponer* una acción, nunca *ejecutarla*
  unilateralmente. Si el usuario hace click en "Cancelar", el frontend
  reenvía `pending_confirmation: {confirmed: false}`; el backend responde
  con un texto de confirmación de que la acción no se ejecutó y continúa la
  conversación con normalidad — no hay estado a medias ni reintento
  automático. El panel guarda en su historial en memoria el mensaje
  `assistant` crudo que el backend adjunta junto a `pending_action` (ver
  1.2) y lo reenvía sin modificarlo al confirmar/cancelar — nunca reconstruye
  ni edita ese mensaje del lado del frontend.
- Integrado en `Layout.tsx` (visible en todas las páginas, mismo criterio
  que `Header`/`MobileNav`).

## 2. Explícitamente fuera de alcance

- Autenticación/autorización de quién puede marcar/descartar o usar el
  asistente — el MVP entero no tiene auth (SPEC-003).
- Persistencia de historial de conversación entre sesiones/recargas.
- El asistente **no** tiene acceso a SQL ni a la capa de persistencia
  directamente — solo tools tipadas sobre casos de uso ya auditados (ver
  sección 0 y 1.2).
- Cambios a los KPIs del Dashboard (`GetDashboardSummaryUseCase`) por causa
  del nuevo estado de triage.
- Cualquier regla de transición de estado restringida (ej. "no se puede
  volver de Descartada a Nueva") — es reversible sin restricciones.

## 3. Verificación exigida antes de aprobar cierre

- Backend: tests unitarios de `UpdateAnomalyTriageStatusUseCase` (existe/no
  existe), del nuevo endpoint PATCH, y de `ClaudeAssistantAdapter` con
  cliente de Anthropic mockeado (nunca la API real en tests) cubriendo al
  menos: respuesta de solo texto, respuesta con `pending_action`, y fallo de
  red cayendo al mensaje de error genérico.
- Verificación end-to-end contra servidor real (no solo tests): al menos un
  cambio de estado de triage y al menos una pregunta real al asistente con
  una llamada real a Claude (con el mismo cuidado de presupuesto de
  siempre — preguntar antes de gastar la llamada).
- Frontend: tests para `TriageStatusBadge`, `AssistantPanel` (incluyendo el
  flujo de confirmación — nunca se ejecuta la acción sin click explícito),
  y los componentes existentes modificados (`AnomaliesFilterBar`,
  `AnomaliesTable`/`TriageList`).
- `pnpm build`/`pnpm lint`/`pnpm test` y `python -m pytest` verificados de
  forma independiente, no solo el reporte de cierre del agente.
