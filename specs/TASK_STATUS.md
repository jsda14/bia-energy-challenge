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
| [SPEC-007](SPEC-007-meter-detail-anomalies.md) | Frontend — Detalle de Medidor y Anomalías | ✅ Aprobado | 1 | 2026-09-25 |
| [SPEC-008](SPEC-008-investigation-evidence-e2e.md) | Frontend — Evidencia Visual de Investigación y E2E | ✅ Aprobado | 1 | 2026-09-25 |
| [SPEC-009](SPEC-009-visual-polish-theming.md) | Frontend — Sistema de Diseño (Teal/Slate), Dark/Light Mode y Fix de Verificación en Navegador | ✅ Aprobado | 1 | 2026-09-25 |
| [SPEC-010](SPEC-010-ux-fixes-and-data-features.md) | Frontend — Fixes de UX y Funcionalidad Pendiente del PDF | ✅ Aprobado | 2 | 2026-09-25 |
| [SPEC-011](SPEC-011-brand-visual-redesign.md) | Frontend — Rediseño Visual "Bia Pulse" (Identidad de Marca Real) | ✅ Aprobado | 2 | 2026-09-25 |

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

---

## SPEC-007 — Frontend: Detalle de Medidor y Anomalías

**Estado:** ✅ Aprobado (2026-09-25, 1 ronda de retrabajo).

**Resumen:** Contenido real de `MeterDetailPage` (ficha de detalle vía
`DetailField` + `MeterHistoryChart`, primer gráfico del proyecto con
ECharts) y de `AnomaliesPage`/`AnomalyDetailPage` (`AnomaliesTable`,
mismo patrón de orden/accesibilidad que `MetersTable` de SPEC-006).
`MeterHistoryChart` permite comparar dinámicamente dos variables del
histórico de lecturas (consumo/voltaje/corriente/power factor) con doble
eje Y y línea de referencia de baseline condicional, usando colores
hardcodeados en `chartColors.ts` sincronizados a mano con
`styles/tokens.css` (decisión tomada en la revisión del plan para evitar
la fragilidad de `getComputedStyle` en jsdom). Primera SPEC de frontend
con cobertura de tests automatizados: 18 tests (Vitest + Testing
Library) sobre los 6 archivos nuevos, setup de Vitest incluido.
`pnpm build`/`pnpm lint`/`pnpm test` verificados de forma independiente
en ambas rondas.

**Retrabajo #1 (motivo):**
1. Bug real de escala en `AnomalyDetailPage.tsx`: `variation_pct` del
   backend ya viene como porcentaje plano (ej. `78.9` = +78.9%), pero el
   código calculaba `(variation_pct * 100).toFixed(1)}%`, multiplicando
   por 100 de más (mostraba "7890.0%" en vez de "78.9%"); el umbral de
   tono crítico también usaba la escala equivocada (`> 0.3` en vez de
   `> 30`). El propio test usaba `variation_pct: 1.0` como fixture, por
   lo que pasaba en verde sin exponer el bug — mismo patrón ya visto
   antes en el proyecto (test que pasa sin probar la propiedad real).
   Corregido: se reemplazó el cálculo a mano por `formatVariationPct()`
   de `domain/formatting.ts` (ya existente, ya usado en el resto del
   proyecto), umbral corregido a `> 30`, fixture del test corregido a un
   valor realista (`78.9`) con la aserción exacta esperada. Gemini
   detectó y corrigió por su cuenta, durante el propio retrabajo, que
   `formatVariationPct` usa `Intl.NumberFormat("es-ES", ...)` y formatea
   con coma decimal ("+78,9%", no "+78.9%") — ajustó el test al
   comportamiento real y correcto en vez de forzar un resultado
   inconsistente con el resto del proyecto.

**Mejora de proceso confirmada:** por primera vez desde que se detectó
el patrón (SPEC-005 y SPEC-006), el agente **no tocó
`specs/TASK_STATUS.md`** en ninguna de las dos entregas de esta SPEC —
la instrucción explícita agregada al SPEC-007 (punto 7 de las
instrucciones al agente) funcionó.

**Veredicto: APROBADO.** El sistema tiene ahora las 5 pantallas
principales del flujo del PDF con contenido real (Dashboard, Meters,
Meter Detail, Anomalies, Anomaly Detail) — solo falta el flujo de
Investigation (SPEC-008).

---

## SPEC-008 — Frontend: Evidencia Visual de Investigación y E2E

**Estado:** ✅ Aprobado (2026-09-25, 1 ronda de retrabajo).

**Resumen:** Cierra el flujo de "Investigation" del PDF sin crear una
página nueva — confirmado en `ARCHITECTURE.md` §7 que ese flujo ya
estaba cubierto por `AnomalyDetailPage` (SPEC-007); lo único pendiente
era "gráfica con la ventana anómala resaltada". `MeterHistoryChart` se
extendió de forma aditiva y 100% retrocompatible con dos props
opcionales (`highlightStart`/`highlightEnd`) que agregan un `markArea`
semitransparente sobre el histórico, aplicado siempre (independiente de
qué variable esté seleccionada, a diferencia del `markLine` de baseline
que solo aplica a consumo). `AnomalyDetailPage` ahora también consulta
`useMeterDetail(anomaly.meter_id)` como query independiente para poder
renderizar el chart con la ventana resaltada, sin que un fallo en esa
consulta afecte el resto de la ficha. Primer test E2E del proyecto
(`e2e/navigation.test.tsx`): 3 escenarios de navegación real entre las 5
rutas usando `createMemoryRouter` con el árbol de rutas real de
`router.tsx`, `apiClient` mockeado con datos completos. 23/23 tests en
total (18 heredados de SPEC-007 sin regresión + 5 nuevos).

**Retrabajo #1 (motivo):** el reporte de cierre original afirmó
`pnpm build` exitoso, pero corriéndolo de forma independiente (no solo
`pnpm test`, que no hace type-checking estricto vía `tsc`) dio un error
real de TypeScript: el mock de `apiClient` en `navigation.test.tsx` se
castea directamente a un tipo `{ get: Mock; post: Mock }` sin pasar por
`unknown`, algo que `tsc -b` rechaza (`TS2352`) pero que Vitest no
detecta porque transpila sin chequeo de tipos estricto. Corregido:
`apiClient as unknown as { get: Mock; post: Mock }`. Gemini reconoció la
causa exacta (Vitest "enmascaró" el error) y esta vez sí confirmó
`pnpm build` de punta a punta antes de reportar — verificado
independientemente, correcto.

**Tercera vez consecutiva sin tocar `specs/TASK_STATUS.md`** (SPEC-007 y
SPEC-008, ambas entregas de cada una) — la instrucción explícita sigue
funcionando de forma sostenida.

**Veredicto: APROBADO.** Con esto el roadmap original de frontend
(SPEC-005 a SPEC-008) queda completo: fundación, Dashboard+Meters,
MeterDetail+Anomalies, e Investigation+E2E — las 5 pantallas del flujo
del PDF con contenido real, primer gráfico interactivo del proyecto, y
primera cobertura de tests automatizados (unitarios + E2E de
navegación) del frontend.

---

## SPEC-009 — Frontend: Sistema de Diseño, Dark/Light Mode y Fixes de Verificación en Navegador

**Estado:** ✅ Aprobado (2026-09-25, 1 ronda de retrabajo).

**Resumen:** Primera vez que el proyecto se levantó de punta a punta
(backend real + frontend real) en un navegador real, en vez de
verificarse solo con tests/curl. Reveló deuda de diseño acumulada desde
SPEC-005: `tokens.css` seguía marcado `/* placeholders hasta SPEC-006 */`
y nunca se había reemplazado. Este SPEC entrega un sistema de diseño
real (paleta Teal/Slate, contraste AA verificado y documentado en ambos
modos), dark/light mode (`useThemeStore` + `ThemeToggle`), corrige el
`yAxis.name` de `MeterHistoryChart` superpuesto sobre los datos, y aplica
breakpoints reales en Dashboard/Detail/Tablas (antes casi sin usar pese a
estar definidos desde SPEC-005).

**Retrabajo #1:** `pnpm build` fallaba por un cast de TypeScript inválido
del mock de `apiClient` en el test E2E heredado (no relacionado al
theming en sí, pero corregido en la misma ronda). Corregido con
`as unknown as {...}`.

**Hallazgos de backend encontrados en la misma sesión de verificación
en navegador (corregidos directamente por los arquitectos, fuera del
flujo de Gemini):**
- Sin `CORSMiddleware` — el frontend real nunca pudo llamar al backend
  desde el navegador (curl/TestClient no aplican política CORS, por eso
  nunca se había detectado). Corregido.
- `GetDashboardSummaryUseCase` nunca usaba `AnomalyRunRepositoryPort`
  (inyectado, no leído) — "Última corrida" se derivaba de
  `max(detected_at)` entre anomalías en vez del `AnalysisRun` real,
  quedando desactualizada si una corrida no detectaba nada nuevo.
  Corregido con `get_latest()` nuevo en el puerto.
- Timestamps naive (`datetime.utcnow()`) sin sufijo de zona — el
  frontend los interpretaba como hora local, mostrando la hora UTC sin
  convertir. Fix estructural: `UTCDateTime` (TypeDecorator) en las 9
  columnas de fecha del sistema, ya que SQLite descarta el `tzinfo` al
  leer de vuelta un datetime aware (confirmado empíricamente) —
  "arreglar solo el origen" no alcanzaba. DB real borrada y re-sembrada.
- `AnomalyRepository.save_many()` sin idempotencia — cada corrida de
  análisis duplicaba las anomalías ya detectadas (confirmado en
  producción: 19 filas para el único incidente real de M-112).
  Corregido con clave natural `(meter_id, type, window_start,
  window_end)`, más un `exists()` que evita gastar una llamada real al
  `AIExplainerPort` (Claude, con costo real) en algo que de todos modos
  se iba a descartar.
- `ClaudeExplainerAdapter` respondía en inglés (prompt sin instrucción
  de idioma) — corregido, verificado con una llamada real a Claude tras
  configurar `BIA_ANTHROPIC_API_KEY` en `backend/.env`.

**Veredicto: APROBADO.** Primera verificación real de integración
frontend↔backend del proyecto — encontró y corrigió 5 bugs de backend
que ningún test unitario/integración había expuesto, todos verificados
end-to-end contra el servidor real (incluyendo confirmación con Claude
real: análisis completo detecta 4 anomalías reales, un segundo análisis
inmediato da 0 nuevas en 0.38s sin gastar llamadas a Claude).

---

## SPEC-010 — Frontend: Fixes de UX y Funcionalidad Pendiente del PDF

**Estado:** ✅ Aprobado (2026-09-25, 2 rondas de retrabajo + 1 fix
directo de los arquitectos).

**Resumen:** 8 hallazgos de la verificación en navegador, incluyendo 2
requisitos del PDF descartados por error en SPEC-006 (búsqueda por
`meter_id`, KPI "Consumo Total"). También: gráfico multi-variable real
(antes limitado a 2 series), fix del bug de merge de ECharts
(`notMerge`), filtro en Anomalías, breadcrumb, botón de análisis
individual por medidor. El hallazgo #8 (`SourceBadge`, indicador visual
de IA real vs. fallback) quedó correctamente **bloqueado** — el schema
actual no expone el origen de la explicación, requiere una decisión de
contrato de backend fuera de alcance de este SPEC.

**Retrabajo #1:** estilos inline en `MeterDetailPage.tsx` (mismo patrón
de SPEC-006), y el `markArea` de highlight dependía de `index === 0`
del array de variables en vez de aplicarse a todas las series activas
(desvío del contrato original de SPEC-008).

**Retrabajo #2 (corrección de diseño de interacción, no bug de
código):** el usuario pidió explícitamente que el selector de variables
del gráfico fuera un único checkbox "Comparar variables" + un
`<select multiple>` (no 4 checkboxes sueltos como la primera entrega, ni
un `<select multiple>` que permitiera quitar `consumption_kwh` como
intentó una iteración intermedia) — consumo siempre es la serie base,
el select solo ofrece las otras 3 variables.

**Fix final directo de los arquitectos (sin pasar por Gemini):** el
`<select multiple>` de la segunda entrega tenía un estilo inline
(`style={{ minHeight: "80px" }}`, la misma clase de violación que se
acababa de pedir corregir) y se veía como un listbox nativo sin
estilizar. Corregido directamente: clase `.select--multi` en
`MeterHistoryChart.module.css` con altura/ancho mínimos y estado
`:checked` tintado con `var(--color-primary)`.

**Tercera vez y más que TASK_STATUS.md no fue tocado** en ninguna de
las 3 entregas de esta SPEC.

**Veredicto: APROBADO.**

---

## SPEC-011 — Frontend: Rediseño Visual "Bia Pulse" (Identidad de Marca Real)

**Estado:** ✅ Aprobado (2026-09-25, 2 rondas de reescritura completa).

**Resumen:** Reemplaza la paleta genérica Teal/Slate de SPEC-009 por un
sistema anclado al logo real de la marca
(`frontend/src/assets/img/bia-icon.jpg` — orbe azul-noche→violeta
eléctrico con rayo lila, descubierto en el repo durante esta sesión).
Fix de un bug de dominio preexistente (`severityToColorToken`:
`MEDIUM`/`HIGH` daban el mismo color, `LOW` era más grave que
`neutral`). Menú mobile colapsable (`MobileNav`) funcional por primera
vez. Sistema de motion "Pulse" (un solo `@keyframes` reutilizado en 3
contextos: botón de análisis, indicador "en vivo", loader de IA) con
soporte de `prefers-reduced-motion`. `AiExplanationBlock` reestructurado
para cubrir "Razón" y "Acción Recomendada" bajo un único ciclo de carga
(antes solo cubría "Razón", dejando "Acción Recomendada" sin loading
visible durante la regeneración). 49/49 tests, `pnpm build`/`pnpm lint`
verificados independientemente.

**Historial de 2 intentos previos (documentado en detalle en
`PROJECT_NOTES.md`, resumen acá):**
1. **v1 (paleta Deep Navy + Electric Lilac, glow genérico):** nunca se
   ejecutó — rechazada en la revisión del plan por ser indistinguible
   del cliché visual "dashboard de IA genérico" (navy+violeta+glow),
   justo lo que se pedía evitar.
2. **v2 (paleta "Copper Signal", industrial/cobre):** sí se ejecutó
   completa (incluyó el primer uso de `react-markdown`/`remark-gfm`,
   que se mantiene en v3), pero fue rechazada por el usuario al verla
   corriendo: paleta sin ninguna relación con el logo real (nunca se
   miró el asset), Dashboard sin jerarquía visual, overlay de loader
   superpuesto con "texto de fondo raro", header sin menú mobile
   funcional, y el bug de severidad confirmado. **v2 nunca llegó a
   commitearse** — quedó reemplazada en el mismo working tree antes de
   cerrar el ciclo de commits, así que no existe en el historial de git
   como una entrega separada.

**Verificación de contraste AA — hallazgo real encontrado por los
arquitectos antes de aprobar el plan:** `--color-primary` propuesto en
modo claro (`#6A63E0`) daba 4.40:1, por debajo del mínimo AA (4.5:1) —
la propia SPEC ya lo marcaba como "estimado, verificar antes de fijar".
Los arquitectos calcularon el ajuste mínimo necesario (`#6660D9`,
4.64:1) antes de mandar la SPEC al agente, en vez de dejarlo como tarea
abierta. El resto de los 12 valores de contraste que el agente declaró
en `tokens.css` fueron verificados independientemente con el mismo
método de cálculo (luminancia relativa WCAG) — los 12 coincidieron
exactamente.

**Cambio de proceso de esta sesión:** por decisión explícita del
usuario, esta implementación la ejecutó **un agente Claude distinto de
Gemini** (Gemini valorado como "flojo para estilos" en esta sesión) —
primera vez que el proyecto usa un agente codificador distinto de
Gemini para una SPEC completa. Mismo protocolo de Boundary Protocol,
Plan Mode, y auditoría independiente aplicado sin cambios.

**Consolidación de versiones:** tras el cierre, se consolidaron los 3
archivos de SPEC (`v1`/`v2`/`v3`) en un único
`specs/SPEC-011-brand-visual-redesign.md` con el contenido final
auditado — mantener 3 versiones por separado no aportaba valor una vez
cerrado el ciclo (v1 nunca se ejecutó, v2 nunca se commiteó). El
razonamiento de diseño de cada iteración queda documentado en la
sección 0 del archivo final y en `PROJECT_NOTES.md`, no como archivos
de spec duplicados.

**Hallazgos menores corregidos directamente por los arquitectos (sin
retrabajo formal):** un comentario de contraste desactualizado en
`tokens.css` (decía 8.24:1, el valor real y correctamente usado era
9.91:1 — solo el comentario estaba desincronizado) y un `color: #ffffff`
hardcodeado en `RunAnalysisButton.module.css` (reemplazado por
`var(--color-bg-elevated, #ffffff)`, mismo patrón ya usado en otros
componentes desde SPEC-010).

**Veredicto: APROBADO.** Pendiente explícito, no resuelto en esta
SPEC: el usuario señaló que quedan ajustes de estilo adicionales que
"siguen sin convencer" — se tratarán como su propia SPEC futura
(número pendiente de asignar), no se mezclan con el cierre de esta.
