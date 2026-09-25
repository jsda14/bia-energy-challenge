# SPEC: SPEC-006 - Frontend: Dashboard y Listado de Medidores

> **Instrucciones para el Agente Codificador:**
> 1. No instales dependencias externas, librerías ni paquetes que no estén explícitamente autorizados en la sección 2.
> 2. No agregues campos adicionales, métodos auxiliares públicos ni endpoints fuera de los contratos descritos en la sección 3. Todo campo que uses en UI debe existir literalmente en `meterSummaryResponseSchema` o `dashboardSummaryResponseSchema` (ya definidos en SPEC-005, sección 3.2 de ese SPEC — no los redefinas, impórtalos).
> 3. Implementa únicamente las tareas listadas en la sección 5 en orden secuencial. Si encuentras un bloqueo, detén la ejecución y solicita aclaración.
> 4. Sigue el **Protocolo de Fronteras de STANDARDS.md sección 2** sin excepción: antes de tocar cualquier archivo, cotéjalo contra la sección 1 de este SPEC; antes de escribir cualquier firma/prop, cotéjalo contra la sección 3. Si algo no encaja, emite `BLOCKED_BY_BOUNDARY: <archivo/firma> — <razón>` y detente.
> 5. Este SPEC construye sobre la fundación de SPEC-005 (ya aprobada) — no reimplementes `api/client.ts`, `api/schemas.ts`, `stores/useAnalysisStore.ts` ni los hooks de `api/queries/`, todos ya existen y están cerrados. Solo se consumen.
> 6. Filtro y orden de la tabla de medidores son **100% client-side** sobre los datos que ya trae `useMeters()` — no se agregan query params ni se modifica ningún hook de `api/queries/`.
> 7. **No modifiques nada de `backend/`** — este SPEC es exclusivamente frontend.

---

## 1. Alcance y Fronteras

* **Objetivo:** Reemplazar los placeholders de `DashboardPage` y
  `MeterListPage` (creados vacíos en SPEC-005) con contenido real: 4
  tarjetas KPI + botón de "Ejecutar análisis" en el Dashboard, y una tabla
  de medidores interactiva (orden + filtro client-side, navegación a
  detalle) en Meter List.

* **En Alcance (In-Scope):**
  - `components/ui/StatCard.tsx` + `.module.css`: tarjeta KPI genérica y
    reutilizable (label, valor, opcionalmente un tono semántico).
  - `components/ui/Badge.tsx` + `.module.css`: badge de color semántico
    genérico (recibe un token `"neutral" | "warning" | "critical"` — ya
    calculado por `severityToColorToken`/`meterStatusToColorToken` de
    `domain/formatting.ts`, no reimplementa ese mapeo).
  - `components/ui/RunAnalysisButton.tsx` + `.module.css`: botón que
    invoca `useRunAnalysis()`, deshabilitado + label alternativo mientras
    `isRunning` (leído de `useAnalysisStore`).
  - `components/feature/MetersTable.tsx` + `.module.css`: tabla de
    medidores con orden por columna (click en header) y fila clickable a
    `/meters/:meterId`. Recibe los medidores ya vía prop (no hace fetch
    ella misma — la página la orquesta).
  - `components/feature/MetersFilterBar.tsx` + `.module.css`: filtro por
    `status` y por `anomaly_severity` (chips o `<select>`, a criterio del
    agente dentro de BEM/CSS Modules) sobre la lista ya cargada.
  - `pages/DashboardPage.tsx`: usa `useDashboardSummary()` +
    `useRunAnalysis()`, renderiza 4 `StatCard` + `RunAnalysisButton` +
    estados de carga/error.
  - `pages/MeterListPage.tsx`: usa `useMeters()`, orquesta
    `MetersFilterBar` + `MetersTable`, estados de carga/error/lista vacía.

* **Fuera de Alcance (Out-of-Scope / Non-Goals):**
  - `MeterDetailPage`, `AnomaliesPage`, `AnomalyDetailPage` — siguen siendo
    placeholders, se implementan en SPEC-007.
  - Cualquier gráfica/chart (histórico de consumo, etc.) — no hace falta
    aquí, no hay serie temporal en `meterSummaryResponseSchema`.
  - Paginación server-side o virtualización de la tabla — el dataset es
    pequeño (12 medidores, confirmado en SPEC-001), una tabla simple sin
    paginación es suficiente. No agregar paginación no pedida.
  - Búsqueda por texto libre (nombre del medidor) — no pedida, no
    agregarla (YAGNI). Solo filtro por `status` y `anomaly_severity`.
  - Modificar `api/client.ts`, `api/schemas.ts`, `api/queries/*`,
    `stores/useAnalysisStore.ts`, `router.tsx`, `AppLayout.tsx`,
    `Header.tsx` — todos ya cerrados en SPEC-005, de solo lectura para
    este SPEC.
  - Cualquier cambio en `backend/`.

* **Archivos Afectados:**
  * **Crear:**
    - `frontend/src/components/ui/StatCard.tsx`
    - `frontend/src/components/ui/StatCard.module.css`
    - `frontend/src/components/ui/Badge.tsx`
    - `frontend/src/components/ui/Badge.module.css`
    - `frontend/src/components/ui/RunAnalysisButton.tsx`
    - `frontend/src/components/ui/RunAnalysisButton.module.css`
    - `frontend/src/components/feature/MetersTable.tsx`
    - `frontend/src/components/feature/MetersTable.module.css`
    - `frontend/src/components/feature/MetersFilterBar.tsx`
    - `frontend/src/components/feature/MetersFilterBar.module.css`
  * **Modificar:**
    - `frontend/src/pages/DashboardPage.tsx` (de placeholder a contenido real)
    - `frontend/src/pages/MeterListPage.tsx` (de placeholder a contenido real)
  * **Prohibido modificar:**
    - Todo `backend/**`
    - `readings.csv`, `events.csv`
    - `ARCHITECTURE.md`, `STANDARDS.md`
    - `frontend/src/api/**`, `frontend/src/stores/**`, `frontend/src/router.tsx`
    - `frontend/src/components/layout/**`
    - `frontend/src/pages/MeterDetailPage.tsx`,
      `frontend/src/pages/AnomaliesPage.tsx`,
      `frontend/src/pages/AnomalyDetailPage.tsx`

---

## 2. Entorno y Dependencias Permitidas

* Ninguna dependencia nueva. Se reutiliza exactamente lo instalado en
  SPEC-005 (`react`, `react-dom`, `react-router-dom`, `@tanstack/react-query`,
  `zustand`, `zod`). Prohibido agregar librerías de tablas (TanStack
  Table, AG Grid, etc.), de gráficas, o de componentes UI — la tabla e
  interactividad se construyen a mano con HTML semántico
  (`<table>`/`<thead>`/`<tbody>`) + CSS Modules, tal como
  `STANDARDS.md` §4.3 exige.

---

## 3. Contratos e Interfaces (Single Source of Truth)

### 3.1 Datos ya disponibles (de SPEC-005, sin cambios)

```typescript
// Ya existen en frontend/src/api/schemas.ts — solo se importan/usan.

// dashboardSummaryResponseSchema →
interface DashboardSummaryResponse {
  anomalies_detected: number;
  high_priority_count: number;
  average_confidence: number | null;
  last_analysis_at: string | null; // ISO datetime
}

// meterSummaryResponseSchema →
interface MeterSummaryResponse {
  meter_id: string;
  name: string;
  status: string;             // usar meterStatusToColorToken()
  consumption_kwh: number;    // usar formatKwh()
  variation_pct: number | null; // usar formatVariationPct()
  anomaly_severity: string | null; // usar severityToColorToken()
}
```

### 3.2 `components/ui/StatCard.tsx` — props

```typescript
interface StatCardProps {
  label: string;
  /** Ya formateado por el caller (ej. formatKwh, o un número plano con "—" si es null). */
  value: string;
  /** Tono opcional para dar énfasis visual (ej. tarjeta de alta prioridad en "warning"). */
  tone?: "neutral" | "warning" | "critical";
}
export function StatCard(props: StatCardProps): JSX.Element { ... }
```

### 3.3 `components/ui/Badge.tsx` — props

```typescript
interface BadgeProps {
  label: string;
  tone: "neutral" | "warning" | "critical";
}
export function Badge(props: BadgeProps): JSX.Element { ... }
```

> `Badge` NO conoce `severity`/`status` como strings de dominio — recibe
> el `tone` ya resuelto por `severityToColorToken`/`meterStatusToColorToken`
> (llamado por el componente padre). Mantiene `Badge` genérico y reusable
> también para SPEC-007/008.

### 3.4 `components/ui/RunAnalysisButton.tsx` — props

```typescript
interface RunAnalysisButtonProps {
  /** meter_id específico, o null para analizar todos los medidores (comportamiento del Dashboard). */
  meterId: string | null;
}
export function RunAnalysisButton(props: RunAnalysisButtonProps): JSX.Element { ... }
```

> Internamente usa `useRunAnalysis()` (mutación) y
> `useAnalysisStore((s) => s.isRunning)` para deshabilitarse + mostrar
> label "Analizando…" mientras `isRunning === true`. No recibe
> `onSuccess`/callbacks por prop — la invalidación de queries ya la
> resuelve `useRunAnalysis` internamente (RN-03 de SPEC-005).

### 3.5 `components/feature/MetersTable.tsx` — props

```typescript
type SortableColumn = "name" | "status" | "consumption_kwh" | "variation_pct" | "anomaly_severity";

interface MetersTableProps {
  meters: MeterSummaryResponse[];
}
export function MetersTable(props: MetersTableProps): JSX.Element { ... }
```

> El estado de orden (columna activa + dirección asc/desc) es estado
> local del componente (`useState`), no global — no pertenece a Zustand.
> Click en un `<th>` alterna: sin-orden → asc → desc → sin-orden (vuelve
> al orden original de `meters`). Un ícono/indicador visual (▲/▼) marca
> la columna y dirección activas. Cada `<tr>` es clickable (o su celda de
> nombre, a criterio del agente) y navega a `/meters/{meter_id}` vía
> `useNavigate()` de `react-router-dom` (ya autorizado, viene con
> `react-router-dom`). Columnas: Nombre, Estado (`Badge`), Consumo
> (`formatKwh`), Variación (`formatVariationPct`, con `Badge` si
> `variation_pct` supera ±30% para que salte a la vista — mismo umbral de
> spike que RN-01 del dominio backend, documentado en SPEC-001; no
> reinventar otro umbral), Severidad de anomalía (`Badge`, o "—" si
> `null`).

### 3.6 `components/feature/MetersFilterBar.tsx` — props

```typescript
interface MetersFilterBarProps {
  statusOptions: string[];   // valores únicos presentes en los datos ya cargados
  severityOptions: string[]; // ídem, excluyendo null
  selectedStatus: string | null;
  selectedSeverity: string | null;
  onStatusChange: (status: string | null) => void;
  onSeverityChange: (severity: string | null) => void;
}
export function MetersFilterBar(props: MetersFilterBarProps): JSX.Element { ... }
```

> `statusOptions`/`severityOptions` se calculan en `MeterListPage` a
> partir de los `meters` ya cargados (`Array.from(new Set(...))`), no son
> una lista hardcodeada de valores posibles — así el filtro nunca ofrece
> una opción que no tenga al menos un medidor real.

### 3.7 `pages/DashboardPage.tsx`

Renderiza, en este orden: título "Dashboard", `RunAnalysisButton`
(`meterId: null`), y una grilla de 4 `StatCard`:

1. "Anomalías detectadas" — `dashboardSummary.anomalies_detected`
2. "Alta prioridad" — `dashboardSummary.high_priority_count`, `tone:
   "warning"` si es `> 0`, si no `"neutral"`
3. "Confianza promedio" — `average_confidence` formateado como
   porcentaje si no es `null` (ej. `${(value * 100).toFixed(0)}%`), o
   `"—"` si es `null`
4. "Última corrida" — `formatDateTime(last_analysis_at)` si no es
   `null`, o `"Nunca"` si es `null`

Mientras `useDashboardSummary()` está en `isLoading`, muestra un texto
simple "Cargando…" (no hace falta skeleton). Si `isError`, muestra un
mensaje de error simple y no crashea.

### 3.8 `pages/MeterListPage.tsx`

Usa `useMeters()`. Mientras `isLoading`: "Cargando…". Si `isError`:
mensaje de error simple. Si la lista está vacía (`meters.length === 0`
tras cargar): mensaje "No hay medidores registrados." Si hay datos:
calcula `statusOptions`/`severityOptions`, mantiene
`selectedStatus`/`selectedSeverity` en `useState` local, filtra
`meters` client-side antes de pasarlos a `MetersTable`, renderiza
`MetersFilterBar` + `MetersTable`.

---

## 4. Reglas de Negocio y Casos Borde

### 4.1 Reglas de Negocio (RN)

- **RN-01 (Filtro y orden 100% client-side):** Ningún filtro/orden de
  esta SPEC dispara una nueva petición HTTP ni modifica `queryKey` — todo
  opera sobre el array ya en memoria de `useMeters()`.
- **RN-02 (Badge nunca decide el mapeo de color):** `Badge` recibe
  siempre un `tone` ya resuelto por `domain/formatting.ts`. Ningún
  componente de esta SPEC reimplementa lógica de mapeo severity/status →
  color — reutilizan `severityToColorToken`/`meterStatusToColorToken`
  existentes.
- **RN-03 (Botón de análisis respeta `isRunning` global):**
  `RunAnalysisButton` se deshabilita mientras `useAnalysisStore().isRunning`
  sea `true`, sin importar qué instancia del botón disparó el análisis
  (si en el futuro hay más de una instancia en pantalla, todas reflejan
  el mismo estado global — CB-02 de SPEC-005 queda resuelto aquí a nivel
  UI).
- **RN-04 (Mobile-first real):** `MetersTable` y las `StatCard` siguen
  `STANDARDS.md` §4.4 — en `xs`/`sm` la tabla puede requerir scroll
  horizontal contenido (con `overflow-x: auto` en un wrapper, sin romper
  el layout de la página), las 4 `StatCard` se apilan en una columna por
  debajo de `md` y pasan a grilla de 2 o 4 columnas desde `md`/`lg`.

### 4.2 Casos Borde (CB)

- **CB-01 (`average_confidence` en 0):** `0` es un valor válido distinto
  de `null` — debe formatearse como `"0%"`, no confundirse con el caso
  `null` ("—").
- **CB-02 (Todos los medidores con la misma severidad/estado):**
  `MetersFilterBar` igual debe renderizar correctamente aunque
  `statusOptions`/`severityOptions` tengan un solo valor.
- **CB-03 (Filtro deja la lista vacía):** Si el filtro seleccionado no
  matchea ningún medidor, `MetersTable` renderiza sin filas (o un mensaje
  simple "Sin resultados para el filtro seleccionado"), sin crashear.
- **CB-04 (Análisis dispara mientras el usuario está en Meter List):**
  Al completarse `useRunAnalysis`, `["meters"]` se invalida (ya lo hace
  el hook de SPEC-005) — `MeterListPage` debe reflejar los datos nuevos
  automáticamente vía TanStack Query, sin lógica adicional en esta
  página.

---

## 5. Plan de Ejecución Secuencial (Atomic Tasks)

- [x] **Paso 1: `Badge` y `StatCard`:** Implementar
  `components/ui/Badge.tsx` y `components/ui/StatCard.tsx` con sus
  `.module.css` (BEM, tokens de `styles/tokens.css`, sin colores
  hardcodeados fuera de los tokens ya definidos).
- [x] **Paso 2: `RunAnalysisButton`:** Implementar consumiendo
  `useRunAnalysis()` + `useAnalysisStore`, según sección 3.4/RN-03.
- [x] **Paso 3: `DashboardPage`:** Reemplazar el placeholder, cablear
  `useDashboardSummary()` + `RunAnalysisButton` + 4 `StatCard`, estados de
  carga/error (sección 3.7).
- [x] **Paso 4: `MetersTable`:** Implementar tabla con orden por columna
  (estado local) y navegación a detalle (sección 3.5).
- [x] **Paso 5: `MetersFilterBar`:** Implementar filtro por
  status/severity (sección 3.6).
- [x] **Paso 6: `MeterListPage`:** Reemplazar el placeholder, orquestar
  `useMeters()` + filtro local + `MetersFilterBar` + `MetersTable`,
  estados de carga/error/lista vacía (sección 3.8).
- [x] **Paso 7: Validación:** `pnpm build` y `pnpm lint` en verde,
  confirmado independientemente por los arquitectos (retrabajo #1:
  estilos inline movidos a CSS Modules, ver `TASK_STATUS.md`).
  Verificación visual manual confirmada el 2026-09-25 contra el backend
  real corriendo — ver SPEC-009 para los hallazgos de esa verificación
  (bug de chart y deuda de diseño, no específicos de esta página).

---

## 6. Verificación y Checklist de Salida (Pipeline de 5 Pasos)

- [x] **1. Validación Arquitectónica:**
  - `components/ui/*` no importa nada de `api/` ni `stores/` — reciben
    todo por props.
  - `components/feature/MetersTable.tsx` y `MetersFilterBar.tsx` no hacen
    fetch propio ni importan hooks de `api/queries/` — reciben `meters`
    ya cargado por prop desde `MeterListPage`.
  - `RunAnalysisButton` es la única excepción autorizada a importar
    `api/queries/useRunAnalysis` y `stores/useAnalysisStore` directamente
    (es un componente de acción, no de presentación pura — mismo criterio
    que la excepción de `Header.tsx` en SPEC-005, documentada en
    `ARCHITECTURE.md` §7.1).
  - Ningún archivo de `api/`, `stores/`, `router.tsx`, `AppLayout.tsx`,
    `Header.tsx` fue modificado — confirmado.
  - `git diff` coincidió únicamente con los archivos autorizados en la
    Sección 1 tras el retrabajo #1. Cero archivos de `backend/` tocados.
- [x] **2. Generación de Tests:**
  - No se exigió suite de tests automatizados en este SPEC (consistente
    con el criterio YAGNI aplicado en SPEC-005) — verificación por build +
    revisión visual manual, confirmada el 2026-09-25.
- [x] **3. Validación de Cobertura:**
  - `pnpm build` compiló sin errores de TypeScript. `pnpm lint` en verde
    — confirmado independientemente en ambas rondas.
- [x] **4. Documentación As-Built:**
  - Comentarios JSDoc breves presentes en los props de cada componente
    nuevo — confirmado.
- [x] **5. Trazabilidad y Estado:**
  - Checklist de este SPEC completado y entrada registrada en
    `specs/TASK_STATUS.md` (1 ronda de retrabajo documentada).
