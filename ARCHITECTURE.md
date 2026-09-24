# ARCHITECTURE.md — Bia Energy Challenge

## 1. Visión

MVP de gestión de medidores eléctricos con detección, explicación, priorización y
recomendación de anomalías vía IA. El flujo central que el sistema debe demostrar:

```
DATOS → ANÁLISIS → ANOMALÍA → EXPLICACIÓN → PRIORIZACIÓN → ACCIÓN
```

El dataset fijo: 12 medidores, 14 días, 4.032 lecturas horarias (`consumption_kwh`,
`voltage_v`, `current_a`, `power_factor`), 4 eventos operativos conocidos
(`events.csv`). `expected_results.csv` es solo del evaluador — nunca se carga en el
sistema.

Casos que el motor de anomalías debe resolver correctamente (ground truth conocido
por inspección de los CSV entregados, no por `expected_results.csv`):

| Medidor | Patrón observado | Clasificación esperada |
|---|---|---|
| M-109 | Desde 2026-09-12 14:00: consumo ~2x baseline, voltaje cae, corriente se dispara, power_factor colapsa (0.93→0.72-0.78). Sin evento operativo. | `REAL_ANOMALY`, `HIGH` |
| M-104 | Step-change sostenido desde 2026-09-11 00:00, coincide con evento `OPERATIONAL_CHANGE` (nueva línea productiva). | `EXPLAINABLE_ANOMALY`, `MEDIUM` |
| M-106 | Caída a near-zero (8-14 kWh vs ~50-65 normal) el 2026-09-08 00:00-11:00, coincide con evento `SCHEDULED_OUTAGE`. | `FALSE_POSITIVE`, `LOW` |
| M-112 | Consumo (kWh) se mantiene normal, pero voltaje/corriente/power_factor muestran saltos erráticos e inconsistentes desde 2026-09-13, coincide con evento `DATA_QUALITY`. | `DATA_QUALITY`, `HIGH` |

Esto confirma que la detección puede (y debe) resolverse con reglas estadísticas
deterministas + correlación de eventos; el LLM se usa para lenguaje natural
(explicación/recomendación), no para decidir si algo es o no una anomalía.

## 2. Estilo arquitectónico: Hexagonal (Ports & Adapters)

Elegido porque:
- El motor de detección de anomalías (dominio) debe ser testeable sin DB ni red.
- La IA (Claude API) es un detalle de infraestructura reemplazable/mockeable — nunca
  debe filtrarse al dominio ni decidir si algo "es" una anomalía real.
- Permite tests unitarios rápidos sobre las reglas de negocio (RN-01..RN-0N) sin
  tocar SQLite ni Anthropic.

```
                     ┌─────────────────────────────┐
                     │   Adapters (inbound/driving) │
                     │  FastAPI routers, CLI seed    │
                     └───────────────┬──────────────┘
                                     │ usa
                     ┌───────────────▼──────────────┐
                     │      Application (use cases)  │
                     │  AnalyzeMeterUseCase,          │
                     │  GetDashboardSummaryUseCase,…  │
                     └───────────────┬──────────────┘
                                     │ depende de (ports)
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
   ┌──────────▼─────────┐ ┌──────────▼─────────┐ ┌──────────▼─────────┐
   │  Domain (core)      │ │ RepositoryPort      │ │ AIExplainerPort     │
   │  Meter, Reading,     │ │ (Meter/Reading/     │ │ (explain+recommend) │
   │  Anomaly, Event      │ │  Anomaly/Event CRUD)│ │                     │
   │  AnomalyDetector     │ └──────────┬──────────┘ └──────────┬──────────┘
   │  (reglas puras)      │            │                       │
   └───────────────────── ┘ ┌──────────▼─────────┐ ┌───────────▼─────────┐
                             │ Adapters (outbound)  │ │ Adapters (outbound)  │
                             │ SQLAlchemy/SQLite     │ │ Claude API client    │
                             └──────────────────────┘ └──────────────────────┘
```

**Regla de dependencia:** las flechas de dependencia siempre apuntan hacia adentro
(domain). Domain no importa nada de `infrastructure/` ni de `adapters/`. Application
depende de puertos (interfaces/protocols), nunca de implementaciones concretas.

## 3. Estructura de carpetas (monorepo)

```
bia-energy-challenge/
├── backend/
│   ├── app/
│   │   ├── domain/                 # Núcleo puro, sin deps externas (excepto pydantic para value objects si aplica)
│   │   │   ├── models/              # Meter, Reading, Event, Anomaly (dataclasses/pydantic)
│   │   │   ├── detection/           # AnomalyDetector, baseline calc, z-score, reglas RN-*
│   │   │   └── ports/               # Protocols: MeterRepositoryPort, ReadingRepositoryPort,
│   │   │                            #   AnomalyRepositoryPort, EventRepositoryPort, AIExplainerPort
│   │   ├── application/             # Casos de uso (orquestan domain + ports)
│   │   │   ├── analyze_meter.py
│   │   │   ├── get_dashboard_summary.py
│   │   │   └── list_anomalies.py
│   │   ├── adapters/
│   │   │   ├── inbound/api/         # FastAPI routers, schemas Pydantic de request/response
│   │   │   └── outbound/
│   │   │       ├── persistence/     # SQLAlchemy models, repos concretos, sqlite engine
│   │   │       └── ai/              # ClaudeExplainerAdapter (usa Anthropic SDK)
│   │   ├── config.py                # Settings (pydantic-settings), env vars
│   │   └── main.py                  # FastAPI app factory, wiring de dependencias (composition root)
│   ├── scripts/
│   │   └── seed_data.py             # Carga readings.csv y events.csv a SQLite
│   ├── tests/
│   │   ├── unit/                    # Domain puro, sin IO
│   │   ├── integration/             # Repos + DB real (SQLite in-memory)
│   │   └── e2e/                     # Cliente FastAPI TestClient
│   ├── data/                        # readings.csv, events.csv (NO expected_results.csv)
│   ├── requirements.txt
│   └── alembic/ (opcional si se decide versionar schema)
├── frontend/
│   ├── src/
│   │   ├── pages/                   # Dashboard, MeterList, MeterDetail, Anomalies, Investigation
│   │   ├── components/
│   │   ├── api/                     # cliente HTTP tipado (fetch/axios + tipos generados o manuales)
│   │   ├── hooks/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
├── specs/                           # SPECs (SDD) + TASK_STATUS.md
├── ARCHITECTURE.md
├── STANDARDS.md
└── README.md
```

## 4. Puertos clave (contratos, no implementación)

- **`MeterRepositoryPort`** — CRUD/lectura de medidores.
- **`ReadingRepositoryPort`** — lecturas por medidor, rango de tiempo, agregaciones.
- **`EventRepositoryPort`** — eventos operativos por medidor/rango.
- **`AnomalyRepositoryPort`** — persistir/consultar anomalías detectadas.
- **`AIExplainerPort`** — `explain(context: AnomalyContext) -> AIExplanation`. Recibe
  hechos ya calculados por el dominio (baseline, variación %, variables que
  cambiaron, evento correlacionado si existe) y devuelve texto de explicación +
  recomendación + nivel de confianza narrativo. **Nunca decide el tipo/severidad** —
  eso lo calcula el `AnomalyDetector` en el dominio con reglas deterministas. El
  adapter concreto (`ClaudeExplainerAdapter`) debe tener un fallback determinista
  (plantilla de texto) si la API falla o no hay API key, para que la demo nunca se
  rompa por falta de red/credenciales.

### 4.1 Agentic Loop (ClaudeExplainerAdapter interno)

El `ClaudeExplainerAdapter` implementa un loop agéntico de 2 pasos:

1. **Tool call → EventQueryTool (MCP)**: el agente consulta eventos operativos
   del medidor en el rango temporal de la anomalía vía un MCP tool local.
2. **Síntesis**: con los eventos recuperados + los hechos calculados por el dominio
   (baseline, variación %, variables afectadas), genera `reason` y `recommended_action`
   en lenguaje natural.

El MCP expone un único tool: `get_events(meter_id: str, from_ts: str, to_ts: str) -> list[Event]`.
El dominio ya calculó tipo/severidad/confianza — el agente solo enriquece la explicación
con contexto operativo. Si el loop falla o no hay API key, el adapter cae al fallback
determinista (plantilla de texto) definido en el puerto.

## 5. Motor de detección de anomalías (dominio)

Enfoque: **reglas estadísticas + correlación de eventos**, determinista y testeable.

1. **Baseline por medidor**: media/mediana móvil de los últimos N días excluyendo el
   punto evaluado (o baseline = média de días previos comparado con el día actual).
2. **Detección de spike/step-change**: variación % vs baseline por encima de umbral
   (p.ej. |Δ| > 30% sostenido ≥ N horas → candidato).
3. **Z-score** sobre consumo para outliers puntuales.
4. **Consistencia eléctrica**: cruce voltage/current/power_factor — si el consumo es
   estable pero V/I/PF se salen de rango físico esperado (p.ej. voltage fuera de
   ~200-245V, power_factor fuera de ~0.85-1.0 de forma errática) → candidato a
   `DATA_QUALITY`, no anomalía de consumo real.
5. **Correlación con `events.csv`**: si existe un evento operativo (`OPERATIONAL_CHANGE`,
   `SCHEDULED_OUTAGE`) solapado en tiempo con la anomalía candidata → reclasifica a
   `EXPLAINABLE_ANOMALY` o `FALSE_POSITIVE` según el tipo de evento y dirección del
   cambio.
6. **Clasificación final** (`type`): `REAL_ANOMALY | EXPLAINABLE_ANOMALY |
   FALSE_POSITIVE | DATA_QUALITY`, con `severity` (`LOW|MEDIUM|HIGH`) y `confidence`
   (0-1) calculados por reglas, no por el LLM.
7. **Explicación/Recomendación**: el `AIExplainerPort` recibe el resultado del paso 6
   junto con los hechos numéricos (variación %, variables afectadas, evento
   correlacionado si aplica) y genera `reason` y `recommended_action` en lenguaje
   natural.

Esto se documenta en detalle (RN-01..RN-0N, casos borde) en el primer SPEC.

## 6. Flujo end-to-end (API)

```
POST /ai/analyze { meter_id? }   → dispara AnalyzeMeterUseCase (uno o todos los medidores)
GET  /ai/analysis/:id            → estado/resultado de un análisis (para polling desde UI)
GET  /dashboard/summary          → KPIs agregados
GET  /meters                     → lista + filtros (todos/normales/alertas/críticas) + búsqueda + orden
GET  /meters/:meterId            → detalle + baseline + variación + estado
GET  /meters/:meterId/readings   → histórico (para gráficas)
GET  /anomalies                  → lista con tipo/severidad/confianza/acción
GET  /anomalies/:id              → detalle de investigación (evidencia, variables, evento relacionado)
```

## 7. Frontend (React + Vite + TypeScript)

Flujo de UX exigido por el PDF: `Dashboard → Medidores → Detalle → Anomalías IA →
Investigación → Acción`. Páginas mínimas:

- **Dashboard**: KPIs (medidores, consumo total, anomalías detectadas, alta
  prioridad, confianza IA agregada, último análisis) + botón **Run AI Analysis**
  con estado del proceso.
- **Meters (lista)**: tabla con filtros (todos/normal/alerta/crítica), búsqueda por
  `meter_id`, orden por consumo/variación/severidad.
- **Meter Detail**: consumo actual, baseline, variación, estado, histórico
  (gráfica), voltaje/corriente/power_factor.
- **Anomalies**: tabla medidor/tipo/severidad/confianza/acción recomendada.
- **Investigation**: qué encontró la IA, variables que cambiaron, comparación vs
  baseline, eventos relacionados, severidad/confianza, acción recomendada,
  evidencia (gráfica con la ventana anómala resaltada).

Cliente HTTP tipado contra los DTOs del backend (compartir tipos vía generación
manual o `openapi-typescript` si se decide más adelante — a definir en SPEC de
frontend).

## 8. Decisiones registradas (ADR-lite)

| Decisión | Alternativas consideradas | Razón |
|---|---|---|
| SQLite + SQLAlchemy | Postgres, in-memory | Cero fricción para el evaluador (un solo `pip install`, sin Docker), suficiente para 4.032 filas, migración a Postgres trivial gracias al ORM. |
| Motor híbrido (reglas + Claude) | Todo-LLM, todo-reglas | Reglas garantizan que los 4 casos del dataset se clasifiquen correctamente y sean testeables; Claude aporta el valor de explicación en lenguaje natural que pide el PDF sin arriesgar la detección a alucinaciones. |
| Hexagonal | Layered clásico, MVC monolítico | Aísla el motor de anomalías (lo más evaluado, 15+15 pts) de IO y de la IA, permitiendo tests unitarios rápidos y swap de Claude por mock sin tocar dominio. |
| Monorepo backend/frontend | Repos separados | Un solo repo Git entregable, más simple para el evaluador clonar y correr. |

## 9. No-goals explícitos del MVP

- Sin autenticación real (login puede ser mock/estético para cumplir el flujo UX del
  PDF, sin JWT/sesiones reales) — a confirmar alcance exacto en SPEC de frontend.
- Sin websockets/streaming real-time — polling simple para estado de análisis.
- Sin multi-tenant, sin roles/permisos.
- Sin entrenamiento de modelos ML — la "IA" es reglas deterministas + LLM para
  lenguaje natural, conforme el PDF permite explícitamente ("la técnica es libre").
