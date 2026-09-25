# SPEC: SPEC-010 - Frontend: Fixes de UX y Funcionalidad Pendiente del PDF

> **Instrucciones para el Agente Codificador:**
> 1. No instales dependencias externas, librerías ni paquetes que no estén explícitamente autorizados en la sección 2.
> 2. No agregues campos adicionales, métodos auxiliares públicos ni endpoints fuera de los contratos descritos en la sección 3.
> 3. Implementa únicamente las tareas listadas en la sección 5 en orden secuencial. Si encuentras un bloqueo, detén la ejecución y solicita aclaración.
> 4. Sigue el **Protocolo de Fronteras de STANDARDS.md sección 2** sin excepción: antes de tocar cualquier archivo, cotéjalo contra la sección 1 de este SPEC; antes de escribir cualquier firma/prop, cotéjalo contra la sección 3. Si algo no encaja, emite `BLOCKED_BY_BOUNDARY: <archivo/firma> — <razón>` y detente.
> 5. **Este SPEC es funcional/UX, NO visual.** No cambies paleta de color, tipografía, ni el sistema de diseño de `tokens.css` — eso es SPEC-011, una SPEC separada. Si algún fix de este SPEC requiere una clase CSS nueva, usá los tokens ya existentes (`var(--color-*)`, `var(--space-*)`), sin inventar valores nuevos.
> 6. Estos hallazgos surgieron de una verificación real en navegador contra el backend corriendo (no solo tests) — cada uno tiene su causa raíz ya diagnosticada en la sección 1, no es necesario volver a investigarla.
> 7. **Este SPEC exige tests automatizados** (Vitest + Testing Library) según `STANDARDS.md` §5 para toda lógica nueva no trivial (búsqueda, `notMerge`, checkboxes multi-variable).
> 8. **`specs/TASK_STATUS.md` NO se toca** — misma instrucción que SPEC-007/008/009, que funcionó en las últimas 3 entregas seguidas.
> 9. **No modifiques nada de `backend/`** — este SPEC es exclusivamente frontend. El backend ya fue corregido directamente por los arquitectos (idempotencia, timestamps UTC, CORS, idioma de Claude) — no relacionado con tu alcance.

---

## 1. Alcance y Fronteras

* **Objetivo:** Cerrar 8 hallazgos de UX/funcionalidad encontrados en la
  verificación en navegador de hoy, incluyendo dos requisitos del PDF que
  se habían descartado por error en SPECs anteriores.

* **Hallazgos y su alcance exacto:**

  1. **Búsqueda por `meter_id` en Medidores (pedida en el PDF, descartada
     por error en SPEC-006).** `MetersFilterBar` necesita un input de
     texto libre que filtre client-side por `meter_id`/`name` (contains,
     case-insensitive), combinándose con los filtros de estado/severidad
     ya existentes (AND lógico entre todos los filtros activos).
  2. **KPI "Consumo total" ausente en Dashboard (pedido en el PDF).**
     Falta una 5ª `StatCard` con la suma de `consumption_kwh` de todos
     los medidores — requiere sumar sobre `useMeters()`, no viene en
     `dashboardSummaryResponseSchema`.
  3. **Selector de gráfico limitado a 2 variables (Serie A/Serie B), no
     multi-variable real.** Reemplazar por checkboxes de las 4 variables,
     graficando todas las marcadas simultáneamente.
  4. **Al destildar "Comparar", la Serie B queda visible en el gráfico
     (bug real).** Causa raíz: `echarts-for-react` hace merge de
     opciones por default (`setOption(option, false)`), no reemplaza —
     falta pasar `notMerge={true}` al componente `<ReactECharts>`.
  4b. **Label del eje X superpuesto sobre el propio gráfico (bug real,
      confirmado visualmente el 2026-09-25 en `AnomalyDetailPage`).**
      Mismo patrón que el bug de `yAxis.name` corregido en SPEC-009,
      pero en el eje X: `grid.bottom: "3%"` no reserva espacio
      suficiente para el nombre de la serie que ECharts posiciona cerca
      del eje temporal, quedando ilegible sobre la última fila de datos.
  5. **Sin filtro en la tabla de Anomalías.** Se vuelve más urgente tras
     el fix de idempotencia del backend (ya no habrá 19 filas
     duplicadas, pero sigue siendo útil filtrar por medidor/tipo/
     severidad en un sistema con muchas anomalías reales).
  6. **Sin breadcrumb/botón "volver" en páginas de detalle.**
     `MeterDetailPage` y `AnomalyDetailPage` no tienen ningún mecanismo
     de regreso explícito más allá del botón atrás del navegador.
  7. **`RunAnalysisButton` no conectado a análisis individual en
     `MeterDetailPage`.** El componente ya soporta `meterId` como prop
     (contrato de SPEC-006) — simplemente nunca se instanció con un
     `meterId` específico fuera del Dashboard.
  8. **Sin indicador visual de "generado por IA" vs. fallback
     determinista.** Hoy `AnomalyDetailPage` muestra `reason`/
     `recommended_action` sin ninguna distinción visual de su origen —
     el usuario no puede saber si es una explicación de Claude o una
     plantilla fija.

* **Fuera de Alcance (Out-of-Scope / Non-Goals):**
  - Cualquier cambio de paleta de color, tipografía, o diseño de marca —
    eso es SPEC-011.
  - Cualquier cambio de layout de tablas a "cards" en mobile — eso
    también es SPEC-011 (es un cambio visual, no funcional).
  - Búsqueda en Anomalías por texto libre (no pedida — el hallazgo #5
    es sobre filtros de valor exacto, mismo patrón que `MetersFilterBar`,
    no búsqueda).
  - Cualquier cambio en `backend/`.
  - Tocar `specs/TASK_STATUS.md`.

* **Archivos Afectados:**
  * **Crear:**
    - `frontend/src/components/feature/AnomaliesFilterBar.tsx`
    - `frontend/src/components/feature/AnomaliesFilterBar.module.css`
    - `frontend/src/components/feature/AnomaliesFilterBar.test.tsx`
    - `frontend/src/components/ui/Breadcrumb.tsx`
    - `frontend/src/components/ui/Breadcrumb.module.css`
    - `frontend/src/components/ui/Breadcrumb.test.tsx`
    - `frontend/src/components/ui/SourceBadge.tsx`
    - `frontend/src/components/ui/SourceBadge.module.css`
    - `frontend/src/components/ui/SourceBadge.test.tsx`
  * **Modificar:**
    - `frontend/src/components/feature/MetersFilterBar.tsx` (+ `.module.css`, `.test.tsx` si existe)
    - `frontend/src/pages/MeterListPage.tsx` (nueva lógica de búsqueda de texto)
    - `frontend/src/pages/DashboardPage.tsx` (+ `.module.css`) (5ª StatCard)
    - `frontend/src/components/feature/MeterHistoryChart.tsx` (+ `.module.css`, `.test.tsx`) (checkboxes multi-variable + `notMerge`)
    - `frontend/src/pages/AnomaliesPage.tsx` (+ `.test.tsx`) (integrar `AnomaliesFilterBar`)
    - `frontend/src/pages/MeterDetailPage.tsx` (+ `.test.tsx`) (Breadcrumb + RunAnalysisButton individual)
    - `frontend/src/pages/AnomalyDetailPage.tsx` (+ `.test.tsx`) (Breadcrumb + SourceBadge)
  * **Prohibido modificar:**
    - Todo `backend/**`
    - `ARCHITECTURE.md`, `STANDARDS.md`, `specs/TASK_STATUS.md`
    - `frontend/src/api/**`, `frontend/src/stores/**`, `frontend/src/router.tsx`
    - `frontend/src/styles/tokens.css` (ningún valor de color/tipografía nuevo)
    - `frontend/src/components/layout/**`
    - `frontend/src/components/ui/Badge.tsx`, `StatCard.tsx`, `DetailField.tsx` (estructura — pueden recibir nuevas instancias con props existentes, pero no se modifican sus contratos)
    - `frontend/src/components/feature/AnomaliesTable.tsx`, `MetersTable.tsx` (estructura — solo `AnomaliesPage.tsx` cambia para pasarles datos ya filtrados)

---

## 2. Entorno y Dependencias Permitidas

* Ninguna dependencia nueva. Todo se resuelve con lo ya instalado
  (`echarts-for-react` ya soporta `notMerge` como prop nativa — no
  requiere actualizar versión).

---

## 3. Contratos e Interfaces (Single Source of Truth)

### 3.1 Búsqueda en `MetersFilterBar` (hallazgo #1)

```typescript
// Prop nueva agregada al contrato existente de SPEC-006:
interface MetersFilterBarProps {
  statusOptions: string[];
  severityOptions: string[];
  selectedStatus: string | null;
  selectedSeverity: string | null;
  searchQuery: string;                          // NUEVO
  onStatusChange: (status: string | null) => void;
  onSeverityChange: (severity: string | null) => void;
  onSearchChange: (query: string) => void;       // NUEVO
}
```

Un `<input type="text" placeholder="Buscar por ID o nombre...">` nuevo en
la barra. `MeterListPage.tsx` mantiene `searchQuery` en `useState` local
(mismo patrón que `selectedStatus`/`selectedSeverity`) y filtra
`meters` por `meter_id.toLowerCase().includes(query.toLowerCase()) ||
name.toLowerCase().includes(query.toLowerCase())`, combinado con AND
respecto a los filtros de estado/severidad ya existentes.

### 3.2 KPI "Consumo total" en Dashboard (hallazgo #2)

`DashboardPage.tsx` agrega `useMeters()` (ya existe el hook) además de
`useDashboardSummary()` — dos queries independientes. Nueva `StatCard`
("Consumo Total", `formatKwh(sum(meters.map(m => m.consumption_kwh)))`)
insertada como la 1ª tarjeta de la grilla (antes de "Anomalías
detectadas"), quedando 5 tarjetas en total. Si `useMeters()` está en
`isLoading`/`isError`, esa tarjeta específica muestra "Cargando…"/"—"
sin bloquear el resto del dashboard (que depende solo de
`useDashboardSummary()`).

### 3.3 `MeterHistoryChart` — multi-variable real + fix de merge (hallazgos #3, #4)

```typescript
// Reemplaza el estado interno de seriesA/seriesB/compareEnabled:
interface MeterHistoryChartProps {
  readings: Reading[];
  baselineKwh: number | null;
  highlightStart?: string;
  highlightEnd?: string;
}
// Sin cambios en las props públicas — el cambio es 100% interno.
```

- Estado interno nuevo: `selectedVariables: Set<ChartVariable>` (o
  `ChartVariable[]`, a tu criterio), default `{"consumption_kwh"}` (una
  sola, igual que el comportamiento actual sin comparar).
- UI: 4 checkboxes (uno por variable de `VARIABLE_LABELS`), en vez de
  los 2 `<select>` + 1 checkbox actuales. Al menos una variable debe
  quedar seleccionada siempre — si el usuario destilda la última
  restante, no se permite (el checkbox se re-marca, o simplemente se
  ignora el evento — a tu criterio, mientras nunca quede el set vacío).
- Cada variable seleccionada es una serie de línea en el chart. Si hay
  2+ variables seleccionadas con escalas muy distintas (ej. kWh y
  power_factor 0-1), usar múltiples ejes Y (`yAxis: [...]`, uno por
  variable activa, alternando `position: "left"`/`"right"` como ya hacía
  el componente para 2 series) — mismo criterio de legibilidad que
  SPEC-007, extendido a N variables en vez de 2.
- El `markLine` de baseline sigue aplicando solo si
  `consumption_kwh` está entre las seleccionadas y `baselineKwh !==
  null` (mismo criterio de SPEC-007, sin cambios).
- El `markArea` de highlight sigue aplicando siempre que
  `highlightStart`/`highlightEnd` estén presentes (mismo criterio de
  SPEC-008, sin cambios).
- **Fix del bug de merge:** agregar `notMerge={true}` a
  `<ReactECharts option={chartOptions} notMerge={true} .../>` — esto
  fuerza que ECharts reemplace completamente la configuración en cada
  cambio de `chartOptions`, en vez de fusionar con el estado visual
  anterior (causa raíz confirmada del bug: series/ejes viejos quedaban
  visibles tras destildar variables).
- **Fix del label del eje X superpuesto (hallazgo #4b):** ajustar
  `grid.bottom` (probar valores mayores a `"3%"`, ej. `"12%"`–`"15%"`, a
  criterio según cuánto espacio requiera el label real) para que el
  nombre de la serie en el eje X no quede montado sobre los últimos
  puntos de datos — mismo criterio que el fix de `grid.top` para el eje
  Y en SPEC-009. Verificar visualmente (no solo que compile) que el
  label queda legible y separado del área de ploteo.
- Colores de cada serie: reusar `CHART_COLOR_SERIES_A`/
  `CHART_COLOR_SERIES_B` de `chartColors.ts` para las primeras 2
  variables seleccionadas (en el orden en que aparecen en
  `VARIABLE_LABELS`, no en el orden de selección del usuario); si hay
  una 3ª/4ª variable seleccionada simultáneamente, agregá 1-2 constantes
  nuevas a `chartColors.ts` siguiendo el mismo patrón de comentario de
  sincronización manual con `tokens.css` (usá tonos ya presentes en la
  paleta actual de `tokens.css`, no inventes colores nuevos — recordá
  instrucción 5, este SPEC no toca la paleta).

### 3.4 `AnomaliesFilterBar` (hallazgo #5)

```typescript
interface AnomaliesFilterBarProps {
  meterIdOptions: string[];
  typeOptions: string[];
  severityOptions: string[];
  selectedMeterId: string | null;
  selectedType: string | null;
  selectedSeverity: string | null;
  onMeterIdChange: (meterId: string | null) => void;
  onTypeChange: (type: string | null) => void;
  onSeverityChange: (severity: string | null) => void;
}
export function AnomaliesFilterBar(props: AnomaliesFilterBarProps): JSX.Element { ... }
```

Mismo patrón exacto que `MetersFilterBar` (3 `<select>`, opciones
calculadas de los datos ya cargados por `useAnomalies()`, filtro
100% client-side, sin nuevos query params). `AnomaliesPage.tsx` se
reestructura para mantener los 3 filtros en `useState` local y pasar
`anomalies` ya filtradas a `AnomaliesTable`, mismo criterio que
`MeterListPage` con `MetersTable`.

### 3.5 `Breadcrumb` (hallazgo #6)

```typescript
interface BreadcrumbProps {
  items: Array<{ label: string; to?: string }>;
  // El último item (sin `to`) se renderiza como texto plano, no link
  // (es la página actual).
}
export function Breadcrumb(props: BreadcrumbProps): JSX.Element { ... }
```

Usa `<Link>` de `react-router-dom` (ya autorizado) para los items con
`to`. `MeterDetailPage` renderiza `<Breadcrumb items={[{label:
"Medidores", to: "/meters"}, {label: meter.name}]} />` antes del `<h1>`;
`AnomalyDetailPage` renderiza `<Breadcrumb items={[{label: "Anomalías",
to: "/anomalies"}, {label: anomaly.type}]} />` de forma análoga.

### 3.6 `RunAnalysisButton` individual en `MeterDetailPage` (hallazgo #7)

Sin cambios de contrato — el componente ya acepta `meterId: string |
null` desde SPEC-006. `MeterDetailPage.tsx` simplemente agrega
`<RunAnalysisButton meterId={meter.meter_id} />` junto al `<h1>` (o donde
visualmente corresponda), análogo a como `DashboardPage` lo usa con
`meterId={null}`.

### 3.7 `SourceBadge` (hallazgo #8)

```typescript
interface SourceBadgeProps {
  /** true si el backend generó esta explicación con el fallback
   * determinista (TemplateExplainerAdapter), false/undefined si vino de
   * Claude real. El frontend NO puede distinguir esto por sí mismo desde
   * los datos actuales — ver nota de bloqueo abajo. */
  source: "ai" | "template";
}
export function SourceBadge(props: SourceBadgeProps): JSX.Element { ... }
```

> **BLOQUEO A RESOLVER ANTES DE IMPLEMENTAR:** `anomalyDetailResponseSchema`
> (cerrado, SPEC-005) **no tiene ningún campo que indique si `reason`/
> `recommended_action` vinieron de Claude o del fallback**. Implementar
> `SourceBadge` con una heurística de frontend (ej. "si el texto está en
> inglés, es fallback" o cualquier detección basada en contenido) sería
> frágil y no es aceptable. Si llegás a este punto del plan y este campo
> no existe en el schema real, emití `BLOCKED_BY_BOUNDARY:
> anomalyDetailResponseSchema — falta campo explanation_source, requiere
> cambio de contrato de backend fuera del alcance de este SPEC` y
> detenete ahí — no implementes el componente sin el dato real. Este
> hallazgo específico (#8) queda pendiente de una vuelta con los
> arquitectos para decidir si se agrega el campo al backend.

---

## 4. Reglas de Negocio y Casos Borde

### 4.1 Reglas de Negocio (RN)

- **RN-01 (Todos los filtros son AND, no OR):** en `MetersFilterBar` y
  `AnomaliesFilterBar`, cuando hay múltiples filtros activos
  simultáneamente (ej. búsqueda + estado + severidad), un item debe
  cumplir TODOS para aparecer — mismo criterio ya usado en SPEC-006.
- **RN-02 (Multi-variable nunca queda vacío):** `MeterHistoryChart`
  nunca permite deseleccionar la última variable activa (CB explícito
  en sección 3.3).
- **RN-03 (Breadcrumb nunca navega a la página actual):** el último item
  de cada `Breadcrumb` no lleva `to` — no genera un link circular a la
  misma página.

### 4.2 Casos Borde (CB)

- **CB-01 (Búsqueda sin resultados):** si `searchQuery` no matchea
  ningún medidor, `MetersTable` sigue usando su mensaje existente de
  "sin resultados" (SPEC-006, sin cambios de contrato ahí).
- **CB-02 (Consumo total con `meters` vacío):** si `useMeters()` devuelve
  lista vacía, la `StatCard` de "Consumo Total" muestra "0,0 kWh"
  (`formatKwh(0)`), no "—" ni error.
- **CB-03 (Filtro de Anomalías deja lista vacía):** mismo criterio que
  CB-03 de SPEC-006 — mensaje simple, sin crashear.

---

## 5. Plan de Ejecución Secuencial (Atomic Tasks)

- [x] **Paso 1: Búsqueda en Medidores** (hallazgo #1, sección 3.1). Tests
  de `MetersFilterBar` (input renderiza, dispara `onSearchChange`) y de
  `MeterListPage` (filtra combinando búsqueda + selects).
- [x] **Paso 2: KPI Consumo Total** (hallazgo #2, sección 3.2). Test de
  `DashboardPage` cubriendo CB-02.
- [x] **Paso 3: Multi-variable + fix de merge + fix de label de eje X en
  `MeterHistoryChart`** (hallazgos #3, #4 y #4b, sección 3.3). Tests:
  selección de 1/2/3/4 variables simultáneas, RN-02 (no permite
  vaciar), y una prueba explícita de que `notMerge` está presente en las
  props pasadas a `ReactECharts` (mock del componente, como ya hace
  `MeterHistoryChart.test.tsx` desde SPEC-007). El fix de `grid.bottom`
  se verifica visualmente (no hay assertion automatizada razonable para
  "el label no se superpone visualmente"), documentado en el Paso 7.
- [x] **Paso 4: `AnomaliesFilterBar` + integración en `AnomaliesPage`**
  (hallazgo #5, sección 3.4). Tests del filtro + de la página.
- [x] **Paso 5: `Breadcrumb`** (hallazgo #6, sección 3.5), integrado en
  `MeterDetailPage` y `AnomalyDetailPage`. Test del componente + smoke
  test de que aparece en ambas páginas.
- [x] **Paso 6: `RunAnalysisButton` individual en `MeterDetailPage`**
  (hallazgo #7, sección 3.6). Test de que se renderiza con el
  `meterId` correcto.
- [x] **Paso 7: `SourceBadge`** (hallazgo #8, sección 3.7) — **BLOQUEADO
  correctamente por Gemini**: `anomalyDetailResponseSchema` no expone el
  origen de la explicación (Claude vs. fallback). Emitió
  `BLOCKED_BY_BOUNDARY` tal como se pedía, sin implementar una
  heurística frágil. `SourceBadge`/`AnomalyDetailPage` no se tocaron
  para este hallazgo — queda pendiente de una decisión de contrato de
  backend (agregar un campo `explanation_source` o similar) antes de
  poder retomarlo en un SPEC futuro.
- [x] **Paso 8: Validación:** `pnpm build`, `pnpm lint`, `pnpm test` en
  verde (incluyendo TODOS los tests heredados), confirmado
  independientemente por los arquitectos. Verificación visual manual de
  los 8 fixes contra el backend real corriendo.

---

## 6. Verificación y Checklist de Salida (Pipeline de 5 Pasos)

- [x] **1. Validación Arquitectónica:**
  - Ningún archivo de `api/`, `stores/`, `router.tsx`, layout, ni
    `tokens.css` fue modificado.
  - `AnomaliesFilterBar`/`MetersFilterBar` no hacen fetch propio.
  - `specs/TASK_STATUS.md` no fue tocado.
  - `git diff` coincide únicamente con los archivos autorizados en la
    Sección 1. Cero archivos de `backend/` tocados.
- [x] **2. Generación de Tests:**
  - Cobertura para los 7-8 hallazgos implementados (según si el #8 se
    bloqueó o no), sin romper ningún test heredado.
- [x] **3. Validación de Cobertura:**
  - `pnpm build`, `pnpm lint`, `pnpm test` en verde.
- [x] **4. Documentación As-Built:**
  - Comentarios JSDoc breves en los componentes/props nuevos.
- [x] **5. Trazabilidad y Estado:**
  - Checklist de este SPEC completado. **La entrada en
    `specs/TASK_STATUS.md` la agregan los arquitectos, no el agente.**
