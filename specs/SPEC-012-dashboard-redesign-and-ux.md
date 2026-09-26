# SPEC: SPEC-012 - Rediseño de Dashboard, Tablas y UX General (MVP Core)

> **Instrucciones para el Agente Codificador:**
> 1. No instales dependencias externas, librerías ni paquetes que no estén explícitamente autorizados en la sección 2.
> 2. No agregues campos adicionales, métodos auxiliares públicos ni endpoints fuera de los contratos descritos en la sección 3.
> 3. Implementa únicamente las tareas listadas en la sección 5 en orden secuencial. Si encuentras un bloqueo, detén la ejecución y solicita aclaración.
> 4. Sigue el **Protocolo de Fronteras de STANDARDS.md sección 2** sin excepción: antes de tocar cualquier archivo, cotéjalo contra la sección 1 de este SPEC; antes de escribir cualquier firma/prop, cotéjalo contra la sección 3. Si algo no encaja, emite `BLOCKED_BY_BOUNDARY: <archivo/firma> — <razón>` y detente.
> 5. **Este SPEC tiene una porción de backend real** (2 extensiones de contrato: consumo agregado de red, eventos por medidor) — no es "solo CSS" como SPEC-009/011. Sección 3.0/3.1 cubren el backend; el resto es frontend.
> 6. **Este SPEC construye sobre todo lo cerrado hasta ahora** (SPEC-005 a SPEC-011 + el fix de `SourceBadge`) — no reimplementes nada ya existente (`Badge`, `StatCard`, `MobileNav`, `MeterHistoryChart`, `AiExplanationBlock`, `SourceBadge`, tokens de `tokens.css`), solo extendelos donde el contrato lo indique.
> 7. **Fuera de alcance explícito, van en un SPEC separado futuro:** asistente operativo conversacional y "Marcar como Atendida/Descartar" de una anomalía — son funcionalidad de negocio nueva, decisión explícita del usuario de no mezclarlas con este rediseño.
> 8. **`specs/TASK_STATUS.md` NO se toca.**
> 9. Todo color/radio/sombra nuevo debe pasar por `styles/tokens.css` como variable — cero valores hardcodeados en archivos `.module.css`.

---

## 0. Contexto y por qué este SPEC

Tras cerrar SPEC-011 (identidad visual "Bia Pulse") y verificar la app corriendo, el usuario identificó que el problema ya no es de paleta/tema — es de **densidad de información y arquitectura de interacción**: el Dashboard es un `<h1>` + grid de `StatCard` planas, la tabla de medidores usa "—" donde debería decir algo operativo, las cards mobile no tienen jerarquía, el chart multi-variable puede saturar el eje Y con 3+ variables simultáneas, y el bloque de explicación de IA es un bloque de texto plano sin escaneabilidad.

Este SPEC ataca esos 7 puntos de UX/diseño de la lista original del usuario (puntos 1-7), más el sub-punto de marcadores de eventos en el chart (parte del punto 9). **Explícitamente fuera de esta tanda** (decisión del usuario, no negociable en este documento): asistente operativo conversacional y flujo de "Atendida/Descartar" — quedan para un SPEC futuro de "mejoras diferenciadoras", separado a propósito para poder explicarlos en la demo como "más allá de lo pedido por la prueba", no mezclados con el MVP core.

---

## 1. Alcance y Fronteras

### 1.1 En Alcance (In-Scope)

**Backend (sección 3.0/3.1):**
- Nuevo endpoint `GET /dashboard/consumption-timeline`: serie temporal de consumo agregado de los 12 medidores (14 días), para la gráfica del Dashboard.
- Extender `GET /meters/{meterId}` con `events: EventResponse[]` — eventos operativos del medidor, para los marcadores en el chart.

**Frontend:**
- Tokens de bordes/elevación en `tokens.css` (sección 3.2).
- Dashboard rediseñado: KPIs con micro-tendencia, gráfica de consumo de red, módulo de Triaje Inmediato, distribución de medidores por estado (sección 3.3).
- `MobileNav`/Header: estandarizar alineación marca-izquierda / controles-derecha (sección 3.4 — ajuste menor, `MobileNav` ya existe).
- `MetersTable`: copy "Dentro de norma" en vez de "—", codificación cromática de variación, micro-indicador de tendencia, affordance de fila clickeable más explícito (sección 3.5).
- Cards mobile de `MetersTable` (mismo componente, breakpoint bajo `--bp-md`): reestructurar en 2 filas con jerarquía clara (sección 3.6).
- `MeterHistoryChart`: prohibir 2+ ejes Y numéricos simultáneos superpuestos — reemplazar por selector segmentado + gráficas sincronizadas o modo normalizado, formato de fecha legible en el eje X, marcadores de eventos operativos (sección 3.7).
- `AiExplanationBlock`: reestructurar el texto en 4 bloques legibles, fix de contraste del header en modo oscuro (sección 3.8).
- `RunAnalysisButton`: loader honesto, sin etapas fabricadas (sección 3.9).

### 1.2 Fuera de Alcance (Out-of-Scope / Non-Goals)

- Asistente operativo conversacional (chatbot/copiloto) — SPEC futuro separado.
- "Marcar como Atendida/Descartar" una anomalía — requiere estado persistente nuevo, SPEC futuro separado.
- Stepper de etapas de análisis ("Lecturas→Línea Base→Correlación→Explicación→Priorización") — descartado explícitamente por el usuario: no refleja los tiempos reales del sistema (análisis sin Claude corre en <1s, con Claude tarda por llamada real a la API, no por "etapas" simulables de forma honesta).
- Cualquier cambio a la paleta de color de SPEC-011 (Bia Pulse) — este SPEC usa esos tokens, no los reemplaza.
- Cualquier cambio a `useAnalysisStore`, `router.tsx`, o los contratos de hooks ya existentes salvo la extensión de schema explícita en 3.1.

### 1.3 Archivos Afectados

**Backend — Modificar:**
- `backend/app/adapters/inbound/api/schemas.py` (nuevo `ConsumptionTimelinePointResponse`, `ConsumptionTimelineResponse`, `EventResponse`; extender `MeterDetailResponse`)
- `backend/app/adapters/inbound/api/dashboard_router.py` (nuevo endpoint)
- `backend/app/adapters/inbound/api/dependencies.py` (nuevo stub de caso de uso)
- `backend/app/main.py` (nuevo builder + override)
- `backend/app/application/dtos.py` (nuevo `ConsumptionTimelinePointDTO`, `ConsumptionTimelineDTO`, `EventDTO`; extender `MeterDetailDTO`)
- `backend/app/application/get_meter_detail.py` (agregar `events` al DTO)

**Backend — Crear:**
- `backend/app/application/get_consumption_timeline.py`
- `backend/tests/unit/application/test_get_consumption_timeline.py`
- `backend/tests/unit/application/test_get_meter_detail_events.py` (o agregar a un archivo existente de tests de `get_meter_detail` si ya existe — verificar antes)

**Frontend — Modificar:**
- `frontend/src/api/schemas.ts` (nuevos schemas Zod, extender `meterDetailResponseSchema`)
- `frontend/src/domain/types.ts` (nuevos tipos inferidos)
- `frontend/src/styles/tokens.css` (tokens de radio/elevación)
- `frontend/src/pages/DashboardPage.tsx` (+ `.module.css`, `.test.tsx`) — rediseño completo
- `frontend/src/components/layout/Header.module.css` (ajuste de alineación)
- `frontend/src/components/feature/MetersTable.tsx` (+ `.module.css`, si existe `.test.tsx`)
- `frontend/src/components/feature/MeterHistoryChart.tsx` (+ `.module.css`, `.test.tsx`) — cambio de contrato (ver 3.7)
- `frontend/src/pages/MeterDetailPage.tsx` (pasar `events` al chart)
- `frontend/src/components/feature/AiExplanationBlock.tsx` (+ `.module.css`, `.test.tsx`) — reestructuración de contenido
- `frontend/src/components/ui/RunAnalysisButton.tsx` (+ `.module.css`) — copy de loader

**Frontend — Crear:**
- `frontend/src/api/queries/useConsumptionTimeline.ts` (+ patrón ya usado por los demás hooks)
- `frontend/src/components/feature/ConsumptionTimelineChart.tsx` (+ `.module.css`, `.test.tsx`)
- `frontend/src/components/feature/TriageList.tsx` (+ `.module.css`, `.test.tsx`) — módulo de "Triaje Inmediato"
- `frontend/src/components/feature/MeterStatusDistribution.tsx` (+ `.module.css`, `.test.tsx`) — distribución por estado

**Prohibido modificar:**
- `frontend/src/api/client.ts`, `frontend/src/stores/**`, `frontend/src/router.tsx`
- `frontend/src/components/ui/Badge.tsx`, `StatCard.tsx` (estructura — solo nuevas instancias con props ya existentes)
- `frontend/src/components/ui/MobileNav.tsx` (lógica — solo `Header.module.css` para alineación, sección 3.4)
- `frontend/src/components/ui/SourceBadge.tsx`
- Cualquier archivo de `backend/` no listado arriba
- `ARCHITECTURE.md`, `STANDARDS.md`, `specs/TASK_STATUS.md`

---

## 2. Entorno y Dependencias Permitidas

Ninguna dependencia nueva. `echarts`/`echarts-for-react` ya autorizados (SPEC-007) cubren tanto `ConsumptionTimelineChart` como los ajustes de `MeterHistoryChart`.

---

## 3. Contratos e Interfaces (Single Source of Truth)

### 3.0 Backend — `GET /dashboard/consumption-timeline`

**Caso de uso nuevo** (`backend/app/application/get_consumption_timeline.py`):

```python
class GetConsumptionTimelineUseCase:
    def __init__(self, meter_repo: MeterRepositoryPort, reading_repo: ReadingRepositoryPort) -> None: ...

    def execute(self) -> ConsumptionTimelineDTO:
        """Agrega consumption_kwh de TODOS los medidores, agrupado por
        timestamp exacto (las lecturas de los 12 medidores comparten la
        misma grilla horaria de readings.csv — no requiere resampling).
        Si dos medidores no comparten exactamente el mismo timestamp
        (no debería ocurrir con el dataset real, pero por robustez), se
        agrupa por timestamp y se suma lo que exista en ese punto —
        nunca se interpola ni se inventa un valor."""
        ...
```

Implementación: `meter_repo.get_all()` + `reading_repo.get_by_meter_id()` por cada medidor (mismo patrón ya usado en `ListMetersUseCase`), acumular en un `dict[datetime, float]` sumando `consumption_kwh` por `timestamp`, devolver ordenado ascendente por tiempo.

**DTOs** (`app/application/dtos.py`):

```python
@dataclass
class ConsumptionTimelinePointDTO:
    timestamp: datetime
    total_consumption_kwh: float

@dataclass
class ConsumptionTimelineDTO:
    points: list[ConsumptionTimelinePointDTO]
```

**Schema de respuesta** (`app/adapters/inbound/api/schemas.py`):

```python
class ConsumptionTimelinePointResponse(BaseModel):
    timestamp: datetime
    total_consumption_kwh: float

class ConsumptionTimelineResponse(BaseModel):
    points: list[ConsumptionTimelinePointResponse]
```

**Router** (`app/adapters/inbound/api/dashboard_router.py`):

```python
@router.get("/consumption-timeline", response_model=ConsumptionTimelineResponse)
def get_consumption_timeline(use_case: GetConsumptionTimelineUseCase = Depends(get_consumption_timeline_use_case)):
    dto = use_case.execute()
    return ConsumptionTimelineResponse.model_validate(dto, from_attributes=True)
```

Mismo patrón de inyección de dependencias que los 6 casos de uso ya existentes en `main.py` (stub en `dependencies.py`, builder + override en `main.py`).

### 3.1 Backend — Eventos en `GET /meters/{meterId}`

**Extender `GetMeterDetailUseCase`** (`app/application/get_meter_detail.py`): agregar un `EventRepositoryPort` al constructor (nueva dependencia inyectada, mismo patrón que `anomaly_repo`), llamar `event_repo.get_by_meter_id(meter_id)`, mapear a `EventDTO`.

**DTOs nuevos:**

```python
@dataclass
class EventDTO:
    event_timestamp: datetime
    event_type: str
    description: str
```

**`MeterDetailDTO` extendido** (agregar un campo, sin tocar los existentes):

```python
@dataclass
class MeterDetailDTO:
    # ... campos existentes sin cambios ...
    events: list[EventDTO]
```

**Schemas de respuesta:**

```python
class EventResponse(BaseModel):
    event_timestamp: datetime
    event_type: str
    description: str

class MeterDetailResponse(BaseModel):
    # ... campos existentes sin cambios ...
    events: list[EventResponse]
```

**`main.py`:** `build_meter_detail_use_case` gana `event_repo=SqlAlchemyEventRepository(session)` en la construcción de `GetMeterDetailUseCase`.

### 3.2 Frontend — Tokens de bordes/elevación (`tokens.css`)

```css
:root {
  /* Radios — de rígido a suave, 3 escalas según tamaño de elemento */
  --radius-pill: 999px;      /* badges, chips, pills — ya en uso, formalizado como token */
  --radius-md: 8px;          /* ya existe — botones, selectores, elementos medianos (sin cambios de valor si ya cumple esto) */
  --radius-lg: 16px;         /* NUEVO — cards, modales, contenedores grandes */

  /* Elevación — sombras consistentes en 3 niveles */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.12);   /* ya existe */
  --shadow-md: 0 4px 12px rgba(var(--color-bg-rgb), 0.24);  /* NUEVO — cards destacadas, dropdowns */
  --shadow-lg: 0 12px 32px rgba(var(--color-bg-rgb), 0.32); /* NUEVO — modales, elementos flotantes */
}
```

> `--radius-lg`/`--shadow-md`/`--shadow-lg` son los únicos tokens nuevos — `--radius-pill` formaliza un valor (999px) que varios componentes (`Badge`, `SourceBadge`, chips de `MeterHistoryChart`) ya usan hardcodeado; reemplazalo por la variable en esos archivos existentes al tocarlos por este SPEC (no hace falta un paso dedicado para esto — donde ya estés editando un `.module.css` de esta lista, aprovechá para reemplazar `999px` por `var(--radius-pill)`).

### 3.3 Dashboard rediseñado

**Estructura de página** (`DashboardPage.tsx`, reemplaza el body actual manteniendo `useDashboardSummary`/`useMeters`/`RunAnalysisButton` ya existentes):

1. **Header** (sin cambios de esta SPEC: título + `RunAnalysisButton`).
2. **Resumen ejecutivo — grilla de `StatCard`** (ya existe, se mantiene: Consumo Total, Anomalías detectadas, Alta prioridad, Confianza promedio, Última corrida). Micro-tendencia: **fuera de alcance real** — no hay dato histórico de "tendencia" en el backend hoy (`dashboardSummaryResponseSchema` no trae comparación con período anterior). No inventar una tendencia falsa: si se implementa, debe ser server-side con dato real; como no está en el alcance de este SPEC (no listado en 3.0), las `StatCard` NO llevan flecha de tendencia en esta ronda — documentar como hallazgo para un SPEC futuro si se quiere resolver bien.
3. **`ConsumptionTimelineChart`** (nuevo componente):
   ```typescript
   interface ConsumptionTimelineChartProps {
     points: { timestamp: string; total_consumption_kwh: number }[];
   }
   ```
   Gráfico de línea simple (ECharts) del consumo agregado de red en 14 días, usando `useConsumptionTimeline()` (nuevo hook, mismo patrón que `useDashboardSummary`). Colores de `chartColors.ts` ya existentes. Loading/error states simples ("Cargando…"/mensaje de error), sin bloquear el resto del Dashboard.
4. **`TriageList`** (nuevo componente):
   ```typescript
   interface TriageListProps {
     anomalies: AnomalySummary[]; // ya tipado en domain/types.ts
   }
   ```
   Filtra `anomalies` donde `severity === "HIGH"` (client-side, sobre los datos ya cargados por `useAnomalies()` — reusar el hook ya existente, no crear uno nuevo), máximo 5 items, cada uno un link directo a `/anomalies/{id}` (mismo patrón de fila clickeable que `AnomaliesTable`, pero en formato de lista compacta, no tabla completa). Si no hay ninguna `HIGH`, mensaje simple "Sin anomalías críticas pendientes."
5. **`MeterStatusDistribution`** (nuevo componente):
   ```typescript
   interface MeterStatusDistributionProps {
     meters: MeterSummary[];
   }
   ```
   Conteo de medidores por `status` (`OK`/`Alert`/`Critical`, ya viene en `meterSummaryResponseSchema`), presentado como 3 cifras con `Badge` de tono correspondiente (`meterStatusToColorToken`) — no un gráfico de torta nuevo, mantiene la disciplina de "sin librerías nuevas ni gráficos no justificados", solo un resumen numérico claro.

**Mobile-first:** todo el layout se apila en una columna en `xs`/`sm`, pasa a grilla de 2 columnas en `md`, y a un layout de 2/3 + 1/3 (chart+triaje a la izquierda, distribución a la derecha) desde `lg` — sin scroll horizontal en ningún viewport.

### 3.4 Header/MobileNav — alineación estandarizada

Ajuste menor en `Header.module.css`: confirmar que `header__brand` (logo + texto) esté alineado a la izquierda, y que `header__actions` (ThemeToggle + botón hamburguesa en mobile) esté agrupado a la derecha con `gap` consistente (`var(--space-2)` o `var(--space-3)`, a definir según se vea mejor). No se toca `MobileNav.tsx` ni `Header.tsx` (lógica) — solo el CSS de espaciado/alineación si hoy no cumple esto (verificar primero, puede que ya esté bien desde SPEC-011).

### 3.5 `MetersTable` — mejoras de presentación (desktop)

- **CB visual:** cuando `variation_pct === null` (medidor sin anomalías), mostrar `"Dentro de norma"` (texto simple, tono `neutral`) en vez de `"—"`. Cuando `anomaly_severity === null`, mismo criterio: `"Sin incidentes"` en vez de `"—"`.
- **Codificación cromática de variación, 3 niveles (contrato cerrado, no a discutir):** reusa exactamente los mismos umbrales que el motor de detección del backend ya usa para severidad (`RN-06` de SPEC-001: `MEDIUM` en 30-80%, `HIGH` en ≥80%) — así el color de la tabla nunca contradice la clasificación real que ya hizo el dominio:
  - `neutral` si `|variation_pct| < 30` (o `null`).
  - `warning` si `30 <= |variation_pct| < 80`.
  - `critical` si `|variation_pct| >= 80`.
  Esto reemplaza el umbral único de `> 30` que usa hoy `MetersTable` (SPEC-006) — no es un valor nuevo inventado, es alinear la UI al criterio que el dominio ya usa.
- **Micro-indicador de tendencia por fila:** un ícono simple (▲/▼, texto o carácter Unicode, no un sparkline — no hay dato histórico por fila para un sparkline real) al lado del valor de variación, ▲ si `variation_pct > 0`, ▼ si `< 0`, nada si `null` o `0`.
- **Affordance de fila clickeable:** la fila ya es clickeable (SPEC-006) — agregar un ícono de chevron (`›`) al final de cada fila (columna nueva sin header de texto, solo visual) para hacer explícito que es interactiva, consistente con el pedido del punto 5 de la lista original para mobile, aplicado también a desktop por consistencia.
- **Filtros combinados:** ya existen (`MetersFilterBar`, SPEC-010) — sin cambios de este SPEC, solo confirmar que siguen funcionando con las columnas nuevas.

### 3.6 `MetersTable` — cards mobile (mismo componente, bajo `--bp-md`)

Reestructurar el CSS de la vista card (ya existe el mecanismo `data-label`/`::before` desde SPEC-011) para el siguiente layout exacto:

```
┌─────────────────────────────────┐
│ M-109              [CRITICAL] [OK]│  ← fila superior: ID + 2 badges (severidad, estado)
│                                   │
│ Consumo          Variación       │  ← fila central, 2 columnas
│ 1.234,5 kWh      ▲ +78,9%        │
│                                 › │  ← chevron de navegación, alineado a la derecha
└─────────────────────────────────┘
```

No es una tabla con labels repetidos verticalmente (patrón actual) — es una card real con `display: grid`/`flex` explícito, sin usar `content: attr(data-label)` para este layout (esa técnica queda para si se necesita en el futuro, acá el diseño pedido es distinto: 2 badges en la esquina superior derecha, no un `data-label` por cada campo).

### 3.7 `MeterHistoryChart` — sin superposición de ejes + marcadores de eventos

**Contrato nuevo** (reemplaza el actual, que permite 2+ variables con ejes Y superpuestos vía `offset`):

```typescript
interface MeterHistoryChartProps {
  readings: Reading[];
  baselineKwh: number | null;
  highlightStart?: string;
  highlightEnd?: string;
  events?: { event_timestamp: string; event_type: string; description: string }[]; // NUEVO
}
```

- **Prohibido:** 2+ ejes Y numéricos visibles simultáneamente en el mismo gráfico (esto es lo que pasaba con 3+ variables seleccionadas vía los chips de SPEC-010/011 — cada una con su propio eje, offset, saturando la vista en mobile).
- **Reemplazo:** selector segmentado (grupo de botones tipo tabs, ya no chips libres de multi-selección) donde el usuario elige **una** variable a la vez para la serie principal — igual que el comportamiento base pre-multi-variable. El modo "comparar" (chip toggle ya existente) pasa a mostrar la segunda variable como **gráfico sincronizado apilado debajo** del primero (dos `<ReactECharts>` o un solo chart con `grid` dual apilado verticalmente, cada uno con su propio eje Y sin compartir espacio horizontal con el otro — ECharts soporta múltiples `grid`/`xAxis`/`yAxis` sincronizados por `axisPointer` con `link`), no como ejes superpuestos en el mismo plano.
- **Formato de fecha en eje X:** usar `formatDateTime`-like abreviado (ej. "12 sep, 14:00" en vez del string ISO crudo `2026-09-12T14:00:00Z`) — configurar `axisLabel.formatter` de ECharts para transformar cada tick, o pre-formatear los timestamps antes de pasarlos como `data` del eje (a criterio de implementación, mientras el eje X nunca muestre un string ISO crudo).
- **Marcadores de eventos:** si `events` viene con datos, agregar un `markLine` (o `markPoint`) por cada evento en `event_timestamp`, con un tooltip que muestre `event_type`/`description` al hover. Color distinto del `markLine` de baseline y del `markArea` de highlight ya existentes (usar `--color-pulse` o una variante, no reusar `--color-critical`/`CHART_COLOR_BASELINE` para no confundir "evento operativo conocido" con "anomalía").

### 3.8 `AiExplanationBlock` — 4 bloques legibles + fix de contraste

**Fix de contraste (bug real a corregir primero, antes de la reestructuración):** verificar en modo oscuro que el header del bloque (título + `SourceBadge` + botón "Regenerar") tenga contraste suficiente — si hay algún color discordante (a confirmar en la implementación, el SPEC no asume cuál es el bug exacto, el agente debe verificarlo contra `tokens.css` real y corregir cualquier hex suelto o token mal aplicado que encuentre).

**Reestructuración de contenido en 4 bloques:** el texto de `reason` (ya renderizado vía `MarkdownText`) se acompaña de una estructura de 4 secciones tituladas, pobladas así:
1. **"Diagnóstico Clave"** — el contenido de `reason` tal cual (ya viene de Claude/template, no se parte más).
2. **"Parámetros Eléctricos Desviados"** — lista de `affected_variables` (ya viene en `AnomalyDetailResponse`, actualmente mostrado aparte en `AnomalyDetailPage` como `DetailField` — mover esa información acá, dentro de `AiExplanationBlock`, ya que conceptualmente es parte de la explicación).
3. **"Correlación con Eventos de Planta"** — `correlated_event` (ídem, mover desde `DetailField` suelto).
4. **"Recomendación Operativa"** — el contenido de `recommended_action` (ya existe en el componente).

> Esto es un cambio de **props** de `AiExplanationBlock`: gana `affectedVariables: string[]` y `correlatedEvent: string | null`, además de los ya existentes. `AnomalyDetailPage.tsx` deja de renderizar esos 2 campos como `DetailField` sueltos (quedan solo en la ficha superior los campos que no son parte de "la explicación": Medidor, Tipo, Severidad, Confianza, Baseline, Observado, Variación, Ventana de Detección — los que sí son evidencia numérica cruda, no explicación en lenguaje natural).

### 3.9 `RunAnalysisButton` — loader honesto

Sin stepper de etapas. El copy actual (`"Analizando..."` mientras `isRunning`) se mantiene, pero se le agrega un indicador visual de progreso indeterminado (ej. una animación sutil de puntos `"Analizando..."` → `"Analizando....."` con `@keyframes`, o un ícono girando con `--motion-*`/`--ease-*` ya existentes de SPEC-011) — sin inventar un contador de "medidor X de 12" que el backend no expone hoy (el endpoint `POST /ai/analyze` no da progreso incremental, es una sola respuesta al terminar). Nada de esto requiere cambios de contrato de `useRunAnalysis`.

---

## 4. Reglas de Negocio y Casos Borde

### 4.1 Reglas de Negocio (RN)

- **RN-01 (Consumo de red es agregación real, no estimación):** `GetConsumptionTimelineUseCase` suma valores reales de `readings`, nunca interpola ni promedia para rellenar huecos — si un timestamp no tiene datos de algún medidor, se suma lo que exista (RN documentada en 3.0).
- **RN-02 (Sin tendencias falsas):** ninguna `StatCard` del Dashboard muestra una flecha/porcentaje de tendencia sin un dato real de backend que la respalde (ver nota en 3.3, punto 2) — no fabricar comparaciones contra períodos que el backend no calcula.
- **RN-03 (Chart nunca superpone 2+ ejes Y numéricos):** verificado explícitamente en el Paso 7 del plan de ejecución, con captura o descripción de cómo se comportan 2, 3, y 4 variables activas.
- **RN-04 (`AiExplanationBlock` no duplica información):** `affected_variables`/`correlated_event` se muestran UNA sola vez (dentro del bloque de 4 secciones) — se eliminan de la ficha superior de `AnomalyDetailPage`, no se dejan en ambos lugares.
- **RN-05 (Eventos en el chart son de solo lectura):** los marcadores de eventos no son clickeables ni interactivos más allá del tooltip — no se agrega navegación ni edición de eventos (no hay esa funcionalidad en el backend).

### 4.2 Casos Borde (CB)

- **CB-01 (Medidor sin eventos):** `events: []` — el chart se renderiza igual, sin marcadores, sin error.
- **CB-02 (Timeline de consumo con datos parciales o vacíos):** si `GetConsumptionTimelineUseCase` no tiene lecturas (caso improbable con el dataset real, pero por robustez), `ConsumptionTimelineChart` muestra el mismo mensaje de "Sin datos históricos" ya usado en `MeterHistoryChart`.
- **CB-03 (`TriageList` sin anomalías HIGH):** mensaje simple, sin crashear (ya especificado en 3.3).
- **CB-04 (Cards mobile con `anomaly_severity`/`variation_pct` null):** mismo criterio que 3.5 (desktop) — "Sin incidentes"/"Dentro de norma" en vez de vacío o guion suelto.
- **CB-05 (Chart con highlight de anomalía Y eventos operativos superpuestos en el tiempo):** ambos se muestran simultáneamente (uno es `markArea`, el otro `markLine`/`markPoint`) — no hay conflicto visual esperado si usan colores distintos (RN de 3.7).

---

## 5. Plan de Ejecución Secuencial (Atomic Tasks)

- [ ] **Paso 1: Backend — `GET /dashboard/consumption-timeline`:** Caso de uso, DTOs, schema, router, DI en `main.py`/`dependencies.py` (sección 3.0). Tests unitarios del caso de uso (agregación correcta, CB-02).
- [ ] **Paso 2: Backend — eventos en `GET /meters/{meterId}`:** Extender `GetMeterDetailUseCase`, DTOs, schema (sección 3.1). Test unitario/integración (medidor con eventos, medidor sin eventos CB-01).
- [ ] **Paso 3: Backend — validación:** `pytest` completo en verde (heredados + nuevos), confirmado antes de tocar frontend.
- [ ] **Paso 4: Frontend — schemas/hooks nuevos:** `consumptionTimelineResponseSchema`, extender `meterDetailResponseSchema` con `events`, `useConsumptionTimeline.ts`. Tipos en `domain/types.ts`.
- [ ] **Paso 5: Tokens de `tokens.css`:** `--radius-lg`, `--shadow-md`, `--shadow-lg`, formalizar `--radius-pill` (sección 3.2).
- [ ] **Paso 6: Dashboard rediseñado:** `ConsumptionTimelineChart`, `TriageList`, `MeterStatusDistribution` + integración en `DashboardPage.tsx` (sección 3.3). Tests de los 3 componentes nuevos + smoke test de la página.
- [ ] **Paso 7: `MeterHistoryChart` — fix de ejes + eventos:** Sección 3.7, el paso más sensible — verificar visualmente (no solo que compile) que 2, 3, y 4 variables activas nunca muestran ejes Y superpuestos. Tests actualizados.
- [ ] **Paso 8: `MetersTable` desktop + mobile:** Secciones 3.5 y 3.6. Tests actualizados/nuevos para el copy de CB, codificación cromática, tendencia por fila.
- [ ] **Paso 9: `AiExplanationBlock` — 4 bloques + fix de contraste:** Sección 3.8, incluyendo la migración de `affected_variables`/`correlated_event` desde `AnomalyDetailPage.tsx`. Tests actualizados.
- [ ] **Paso 10: `RunAnalysisButton` — loader honesto:** Sección 3.9.
- [ ] **Paso 11: Header/MobileNav — alineación:** Sección 3.4 (verificar primero si ya cumple, ajustar solo si no).
- [ ] **Paso 12: Validación final:** `pnpm build`, `pnpm lint`, `pnpm test` en verde. Verificación visual manual completa: Dashboard en 3 viewports, `MetersTable` desktop y mobile, `MeterHistoryChart` con 1/2/3/4 variables activas y con/sin eventos, `AiExplanationBlock` en modo oscuro y claro.

---

## 6. Verificación y Checklist de Salida (Pipeline de 5 Pasos)

- [ ] **1. Validación Arquitectónica:**
  - Backend: nuevo caso de uso sigue el mismo patrón hexagonal que los 6 existentes (puerto → adapter → caso de uso → router, inyección vía `dependencies.py`/`main.py`).
  - Frontend: componentes nuevos (`ConsumptionTimelineChart`, `TriageList`, `MeterStatusDistribution`) reciben datos por props o usan hooks ya establecidos (`useAnomalies`, `useMeters`) — no hacen fetch propio fuera del patrón ya existente.
  - `specs/TASK_STATUS.md` no fue tocado.
  - `git diff` coincide únicamente con los archivos autorizados en la Sección 1.3.
  - Cero dependencias nuevas.
- [ ] **2. Generación de Tests:**
  - Backend: cobertura de los 2 casos de uso nuevos/extendidos.
  - Frontend: cobertura de los 3 componentes nuevos del Dashboard + los componentes modificados (`MeterHistoryChart`, `MetersTable`, `AiExplanationBlock`).
  - Todos los tests heredados de SPEC-005 a SPEC-011 + el fix de `SourceBadge` siguen pasando.
- [ ] **3. Validación de Cobertura:**
  - `pytest` (backend) y `pnpm build`/`pnpm lint`/`pnpm test` (frontend) en verde.
- [ ] **4. Documentación As-Built:**
  - Comentarios JSDoc/docstrings en los contratos nuevos (casos de uso, componentes).
- [ ] **5. Trazabilidad y Estado:**
  - Checklist de este SPEC completado. La entrada en `specs/TASK_STATUS.md` la agregan los arquitectos, no el agente.
