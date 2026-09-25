# TASK_STATUS.md — Índice de SPECs

Índice global de todos los SPECs del proyecto. Cada fila resume el estado de
un SPEC; el detalle granular de tareas (checklists de sección 5/6) vive
dentro del propio archivo `SPEC-XXX-*.md`. Este archivo se actualiza cada vez
que un SPEC cambia de estado (aprobado, en retrabajo, bloqueado).

| SPEC | Título | Estado | Retrabajos | Última actualización |
|---|---|---|---|---|
| [SPEC-001](SPEC-001-domain-anomaly-detection.md) | Dominio: Modelos y Motor de Detección de Anomalías | ✅ Aprobado | 5 | 2026-09-24 |
| [SPEC-002](SPEC-002-persistence-and-seed.md) | Persistencia (SQLite/SQLAlchemy) y Seed de Datos | ✅ Aprobado | 1 | 2026-09-24 |
| [SPEC-003](SPEC-003-use-cases-and-api.md) | Casos de Uso, Persistencia de Anomalías y API FastAPI | ✅ Aprobado | 2 | 2026-09-24 |
| [SPEC-004](SPEC-004-claude-explainer-adapter.md) | IA — Adapter Claude (agentic loop, tool-use nativo) | ✅ Aprobado | 0 | 2026-09-24 |
| [SPEC-005](SPEC-005-frontend-foundation.md) | Frontend — Fundación (Setup, Cliente HTTP, Diseño Base, Layout) | ✅ Aprobado | 1 | 2026-09-24 |
| [SPEC-006](SPEC-006-dashboard-meter-list.md) | Frontend — Dashboard y Listado de Medidores | ✅ Aprobado | 1 | 2026-09-25 |

**Leyenda de estado:** ⬜ No iniciado · 🟡 En progreso / en retrabajo · 🔴 Bloqueado · ✅ Aprobado

---

## SPEC-001 — Dominio: Modelos y Motor de Detección de Anomalías

**Estado:** ✅ Aprobado (2026-09-24, tras 5 rondas de retrabajo y 6 auditorías).

**Resumen:** Modelos de dominio inmutables (`Meter`, `Reading`, `Event`,
`AnomalyRecord`) y motor de detección determinista (`AnomalyDetector`),
verificado contra las 4.032 lecturas reales completas del dataset. Los 4
casos documentados por el PDF (M-109, M-104, M-106, M-112) clasifican
correctamente en una sola ventana cada uno; los 8 medidores restantes dan 0
falsos positivos. 28 tests unitarios, 93% de cobertura sobre
`domain/detection/` + `domain/models/`.

**Historial de retrabajos** (motivo de cada ronda, resumido):
1. Bug de severidad en `DATA_QUALITY` (RN-06 solo miraba voltaje, no
   power_factor) + fragmentación de ventanas por bloqueo compartido entre
   fases.
2. Reordenar fases arregló M-112 pero fragmentó M-109 (power_factor
   colapsado cae en clustering eléctrico) + regla de reclasificación no
   autorizada agregada por el agente (revertida).
3. Tolerancia de gap dentro de la racha de consumo para que un valle
   nocturno normal no corte un incidente sostenido.
4. Tolerancia de gap insuficiente ante contexto real completo — descubierto
   que la variación diurna natural del dataset (47-59%) ya supera el umbral
   de spike (30%) por sí sola.
5. Rediseño de RN-01/RN-02: baseline por franja horaria (comparar cada hora
   contra su propio histórico horario) en vez de baseline plano de 24h —
   resuelve el problema de raíz para los 12 medidores a la vez.

**Lección de proceso más importante:** nunca validar con fixtures recortados
"a medida" del caso que se quiere probar — solo el histórico 100% completo
real revela interacciones con el baseline móvil. Ver `PROJECT_NOTES.md`
(bitácora personal, no versionada) para el detalle completo de cada
auditoría.

---

## SPEC-002 — Persistencia (SQLite/SQLAlchemy) y Seed de Datos

**Estado:** ✅ Aprobado (2026-09-24, 1 ronda de retrabajo).

**Resumen:** `MeterRepositoryPort`/`ReadingRepositoryPort`/
`EventRepositoryPort` como `Protocol`, implementados por adapters
SQLAlchemy que nunca exponen filas ORM fuera de `persistence/`. Script de
seed idempotente verificado corriendo dos veces contra la base de datos
real: 12 medidores, 4.032 lecturas, 4 eventos, conteos idénticos en ambas
corridas. 46 tests (28 unit heredados sin tocar + 18 integration nuevos).

**Alcance:** Solo `Meter`/`Reading`/`Event` (repos + seed desde CSV real).
`AnomalyRepositoryPort` queda para SPEC-003, cuando exista el caso de uso que
genera y persiste anomalías.

**Retrabajo (motivo):**
1. `MeterRepositoryPort.save()` se entregó con un parámetro `created_at`
   no autorizado, desviándose de la firma exacta definida en la sección 3.1
   del SPEC — descubierto en auditoría, no reportado por el propio agente
   (su declaración de Fase 0 afirmó que no había fronteras violadas). Motivó
   endurecer `STANDARDS.md` sección 2 (Boundary Protocol) para cubrir
   explícitamente firmas/contratos, no solo rutas de archivo. Fix: firma
   restaurada exacta, `created_at` resuelto con `datetime.utcnow()` dentro
   del repo en vez de recibirlo como parámetro.

**Hallazgo menor no bloqueante:** `Meter.id` se construye distinto en
`seed()` (usa el string `meter_id`) que en los métodos de lectura del repo
(usa el entero autoincremental de la tabla) — inconsistencia latente sin
consumidor real todavía. A vigilar si SPEC-003 llega a depender de
`Meter.id`.

---

## SPEC-003 — Casos de Uso, Persistencia de Anomalías y API FastAPI

**Estado:** ✅ Aprobado (2026-09-24, 2 rondas de retrabajo).

**Resumen:** Conecta el motor de detección (SPEC-001) con la persistencia
(SPEC-002) vía 6 casos de uso de aplicación, expuestos por una API FastAPI
de 8 endpoints. `POST /ai/analyze` corre el `AnomalyDetector` real y
persiste resultados; `GET /anomalies` los devuelve con explicación en
lenguaje natural vía `TemplateExplainerAdapter` (fallback determinista —
Claude real es SPEC-004). Primer pipeline end-to-end funcional del
proyecto: HTTP → caso de uso → detección → explicación → persistencia
atómica → respuesta. 64 tests, los 4 casos del PDF verificados contra el
servidor real (no solo tests): M-109 `REAL_ANOMALY/HIGH`, M-104
`EXPLAINABLE_ANOMALY/MEDIUM`, M-106 `FALSE_POSITIVE/LOW`, M-112
`DATA_QUALITY/HIGH`.

**Alcance:** incluye `AnomalyRepositoryPort` + `AnalysisRun` (a diferencia
de SPEC-002, que los dejó fuera a propósito hasta que existiera el caso de
uso que los necesita). `ClaudeExplainerAdapter` real, ejecución asíncrona,
y autenticación quedan fuera — SPEC-004 y siguientes.

**Retrabajos (motivo de cada ronda):**
1. **Sesión compartida por request.** La primera entrega tenía cada
   `get_X_repo()` en `main.py` abriendo su propia `Session` independiente
   — sin atomicidad entre persistir anomalías y persistir el `AnalysisRun`
   que las resume. Se introdujo el patrón "una sesión por request" de
   FastAPI (`Depends(get_db_session)`). En el camino, Gemini atrapó
   correctamente (vía Boundary Protocol) que `AnomalyRepositoryPort` no
   podía retornar `AnomalyRecord` en sus métodos de lectura — ese modelo no
   tiene `id`/`reason`/`recommended_action` — lo que llevó a introducir
   `PersistedAnomaly` como modelo nuevo.
2. **Atomicidad real, no solo sesión compartida.** El retrabajo #1 resolvió
   el ciclo de imports pero cada repo seguía haciendo su propio
   `session.commit()` dentro de la sesión compartida — la sesión compartida
   por sí sola no daba atomicidad. Se movió `commit()`/`rollback()` de los
   5 repos de escritura (3 de SPEC-002, ya cerrado — reapertura autorizada
   explícitamente por escrito en el propio SPEC-003) al único punto que
   controla el ciclo de vida completo de la operación
   (`get_db_session`/`seed_data.py`). Verificado con un test que prueba el
   escenario real (flush → rollback → sesión nueva → 0 filas), exigido sin
   condicionales después de que el plan inicial de Gemini lo dejara como
   "si hace falta". Antes de confiar en el test, se verificó
   independientemente que el engine `sqlite:///:memory:` realmente
   comparte conexión entre sesiones (descartando un falso positivo por
   bases aisladas).

**Nota de proceso:** primer caso del proyecto en que un retrabajo de un
SPEC posterior (SPEC-003) requiere tocar y reabrir código de un SPEC ya
cerrado y auditado (SPEC-002) — documentado y autorizado explícitamente por
escrito en el SPEC antes de ejecutar, no de forma implícita.

---

## SPEC-004 — IA: Adapter Claude (Agentic Loop)

**Estado:** ✅ Aprobado (2026-09-24, 0 rondas de retrabajo — el diseño
completo se validó en Plan Mode antes de ejecutar, ver nota abajo).

**Resumen:** `ClaudeExplainerAdapter` implementa `AIExplainerPort` vía el
SDK oficial de Anthropic con tool-use nativo (sin servidor MCP separado):
un agentic loop de hasta 3 iteraciones donde Claude puede llamar
`get_events` (consulta eventos reales vía `EventRepositoryPort`) antes de
entregar su respuesta final estructurada vía la tool `submit_explanation`.
Cualquier fallo (red, timeout, argumentos faltantes, iteraciones agotadas)
cae silenciosamente al `TemplateExplainerAdapter` ya existente (SPEC-003,
sin modificarlo) — verificado end-to-end sin API key configurada (CB-01):
el sistema completo sigue funcionando idéntico a SPEC-003. 69 tests (64
heredados sin cambios + 5 nuevos con cliente de Anthropic mockeado, nunca
la API real).

**Por qué 0 retrabajos, a diferencia de los SPECs anteriores:** se usó
Plan Mode (Gemini 3.1 Pro) desde el principio — el plan de implementación
se revisó y corrigió DOS VECES antes de autorizar la ejecución:
1. Primera revisión: el plan proponía `explain(anomaly: PersistedAnomaly)`,
   pero el contrato real y cerrado de `AIExplainerPort` (SPEC-001) recibe
   `AnomalyRecord` — `PersistedAnomaly` ni siquiera existe en el punto
   donde `explain()` se invoca (antes de persistir). Corregido en el plan
   antes de tocar código.
2. Segunda revisión: se pidió hacer explícito el manejo de múltiples
   `tool_use` blocks en una misma respuesta de Claude (incluyendo tools
   desconocidas) para no dejar `tool_use_id` huérfanos si la conversación
   continuara — el plan lo incorporó con un test dedicado
   (`test_explain_handles_multiple_tools_and_unknown`).

**Hallazgo corregido tras la implementación (no requirió retrabajo de
Gemini, arreglado directamente):** `claude_model` quedó con el default
`"claude-3-5-sonnet-20240620"` en vez de `"claude-sonnet-4-6"` como fija
la sección 3.1 del SPEC — corregido en una línea antes de commitear.

**Lección de proceso:** revisar el plan ANTES de ejecutar (Plan Mode) —
en vez de auditar el código después de escrito — evitó por primera vez en
el proyecto una ronda completa de retrabajo. Los 2 problemas que en
SPECs anteriores se hubieran descubierto en auditoría post-implementación
(con el costo de un ciclo completo de retrabajo) se corrigieron en el
plan mismo, antes de que existiera código que deshacer.

---

## SPEC-005 — Frontend: Fundación (Setup, Cliente HTTP, Diseño Base, Layout)

**Estado:** ✅ Aprobado (2026-09-24, 1 ronda de retrabajo).

**Resumen:** Inicialización del proyecto frontend bajo la arquitectura por
capas estipulada (`domain/`, `api/`, `stores/`, `components/`, `pages/`).
Cliente HTTP con `fetch` nativo validado estrictamente mediante 7 schemas
Zod (réplica exacta de los contratos reales del backend, confirmada campo
por campo). Routing con React Router v6 (5 páginas placeholder) y layout
con un indicador visual conectado a Zustand (`useAnalysisStore`, patrón
`getState()` correcto dentro de los callbacks de TanStack Query). Tokens
de diseño mobile-first con los 8 breakpoints exactos de `STANDARDS.md`
§4.4. `pnpm build` y `pnpm lint` (eslint) compilan/pasan sin errores —
confirmado de forma independiente en ambas rondas.

**Retrabajo #1 (motivo):**
1. El agente había editado `TASK_STATUS.md` sin autorización y corrompió
   el encoding de la sección agregada (tildes rotas, un tab literal en
   medio de "tokens.css") — reparado directamente por los arquitectos, sin
   pedir retrabajo de Gemini para esto.
2. El reporte de cierre original afirmó haber generado un `walkthrough.md`
   que no existe en ninguna parte del repositorio — discrepancia entre lo
   reportado y lo verificable, no corregida (no era código, solo un
   recordatorio de no confiar en el reporte sin auditar el filesystem).
3. Se había instalado `oxlint` en vez de `eslint` (único linter autorizado
   en la sección 2 del SPEC) — corregido: `oxlint`/`.oxlintrc.json`
   eliminados, `eslint.config.js` (flat config) + plugins estándar de
   React/TS agregados. `pnpm lint` confirmado en verde de forma
   independiente.
4. Bug real en `useRunAnalysis.ts`: si `POST /ai/analyze` fallaba, se
   llamaba `finishRun("")` con un comentario en el código admitiendo que
   el caso no estaba resuelto. Corregido: `finishRun` ahora acepta
   `string | null` (ajuste menor y autorizado al contrato de la sección
   3.4 del SPEC), `useRunAnalysis` llama `finishRun(null)` en el camino de
   fallo — sin más estado ambiguo.

**Lección de proceso:** el reporte de "walkthrough.md generado" resultó
falso (el archivo nunca existió) — reforzó, una vez más, que ningún
reporte de cierre se acepta sin verificar el filesystem/build/tests de
forma independiente, sin importar cuán detallado suene el reporte.

---

## SPEC-006 — Frontend: Dashboard y Listado de Medidores

**Estado:** ✅ Aprobado (2026-09-25, 1 ronda de retrabajo).

**Resumen:** Contenido real de `DashboardPage` (4 `StatCard` con los KPIs
de `dashboardSummaryResponseSchema` + `RunAnalysisButton` conectado a
`useRunAnalysis`/`useAnalysisStore`) y `MeterListPage` (`MetersTable` con
orden por columna y `MetersFilterBar` con filtro por `status`/
`anomaly_severity`, ambos 100% client-side sobre los datos ya cargados por
`useMeters`). Componentes genéricos nuevos (`Badge`, `StatCard`) sin
lógica de negocio propia; `RunAnalysisButton` documentado como la única
excepción de esta SPEC autorizada a importar `api/`/`stores/` directamente
(mismo criterio que la excepción de `Header.tsx` en SPEC-005). Se agregó
accesibilidad de teclado a la tabla (headers ordenables como `<button>`,
filas con `role="button"`/`tabIndex`/captura de Enter y Space) como
condición añadida durante la revisión del plan, antes de escribir código.
`pnpm build` y `pnpm lint` verificados de forma independiente en ambas
rondas.

**Plan Mode:** el plan de implementación se revisó antes de ejecutar
código — se sumó como condición la accesibilidad de teclado de la tabla,
no contemplada explícitamente en la SPEC. 0 rondas de retrabajo sobre la
lógica funcional; el único retrabajo fue puramente de estilos (ver abajo).

**Retrabajo #1 (motivo):**
1. `DashboardPage.tsx` y `MeterListPage.tsx` se entregaron con estilos
   inline (`style={{...}}`) para el layout de contenedores/grillas,
   violando `STANDARDS.md` §4.3 (regla explícita del proyecto: sin
   estilos inline, todo vía CSS Modules + BEM) — no declarado como
   excepción en el plan aprobado. Corregido: `DashboardPage.module.css` y
   `MeterListPage.module.css` creados con clases BEM
   (`.dashboard`, `.dashboard__header`, `.dashboard__stats-grid`,
   `.meter-list`, `.meter-list__title`), sin tocar lógica de fetching ni
   de estado. `pnpm build`/`pnpm lint` reconfirmados en verde de forma
   independiente tras el retrabajo.

**Hallazgo repetido de proceso (no bloqueante, ajeno al código):** el
agente volvió a editar `TASK_STATUS.md` sin autorización (no estaba en la
sección 1 de archivos a modificar del plan aprobado) y corrompió su
encoding de la misma forma que en SPEC-005 (mojibake, mezcla de
terminadores de línea) — reparado directamente por los arquitectos a
partir de la última versión limpia commiteada. Segunda vez que ocurre;
a vigilar en las próximas entregas.
