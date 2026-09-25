# SPEC: SPEC-007 - Frontend: Detalle de Medidor y Anomalías

> **Instrucciones para el Agente Codificador:**
> 1. No instales dependencias externas, librerías ni paquetes que no estén explícitamente autorizados en la sección 2.
> 2. No agregues campos adicionales, métodos auxiliares públicos ni endpoints fuera de los contratos descritos en la sección 3. Todo campo que uses en UI debe existir literalmente en `meterDetailResponseSchema`, `readingResponseSchema`, `anomalySummaryResponseSchema` o `anomalyDetailResponseSchema` (ya definidos en SPEC-005 — no los redefinas, impórtalos).
> 3. Implementa únicamente las tareas listadas en la sección 5 en orden secuencial. Si encuentras un bloqueo, detén la ejecución y solicita aclaración.
> 4. Sigue el **Protocolo de Fronteras de STANDARDS.md sección 2** sin excepción: antes de tocar cualquier archivo, cotéjalo contra la sección 1 de este SPEC; antes de escribir cualquier firma/prop, cotéjalo contra la sección 3. Si algo no encaja, emite `BLOCKED_BY_BOUNDARY: <archivo/firma> — <razón>` y detente.
> 5. Este SPEC construye sobre SPEC-005 (fundación) y SPEC-006 (Dashboard + Meter List), ambas cerradas — no reimplementes `api/`, `stores/`, `router.tsx`, `Badge`, `StatCard`, `RunAnalysisButton`, solo se consumen/reutilizan.
> 6. **Este SPEC exige tests automatizados** (Vitest + Testing Library) según la sección 5.1 de `STANDARDS.md` — no es opcional como lo fue en SPEC-005/006. Ver sección 5 de este documento para el detalle exacto de qué se testea.
> 7. **`specs/TASK_STATUS.md` NO se toca bajo ninguna circunstancia** — en las dos SPECs de frontend anteriores este archivo fue editado sin autorización y su encoding quedó corrupto ambas veces. Si tu flujo de trabajo interno necesita un archivo de notas/progreso, usa un archivo fuera del repositorio (o si debe estar dentro, un archivo nuevo bajo `frontend/.scratch/` — nunca versionado, nunca `specs/TASK_STATUS.md`).
> 8. **No modifiques nada de `backend/`** — este SPEC es exclusivamente frontend.

---

## 1. Alcance y Fronteras

* **Objetivo:** Reemplazar los placeholders de `MeterDetailPage` y
  `AnomaliesPage`/`AnomalyDetailPage` con contenido real: el detalle de un
  medidor con un gráfico histórico comparativo (ECharts, selección
  dinámica de variables), y el listado + detalle de anomalías detectadas.

* **En Alcance (In-Scope):**
  - `components/feature/MeterHistoryChart.tsx` + `.module.css`: gráfico
    de línea temporal sobre `readings` de un medidor, con selectores para
    que el usuario elija qué variable(s) comparar.
  - `components/feature/AnomaliesTable.tsx` + `.module.css`: tabla de
    anomalías (mismo patrón de orden por columna + accesibilidad que
    `MetersTable` de SPEC-006), sin filtro por ahora (no pedido).
  - `components/ui/DetailField.tsx` + `.module.css`: par
    label/valor genérico reutilizable para las fichas de detalle (medidor
    y anomalía) — evita repetir el mismo layout de "campo: valor" a mano
    en cada página.
  - `pages/MeterDetailPage.tsx`: usa `useMeterDetail(meterId)`, muestra
    ficha de datos del medidor (`DetailField` × N) + `MeterHistoryChart`.
  - `pages/AnomaliesPage.tsx`: usa `useAnomalies()`, muestra
    `AnomaliesTable` con navegación a `/anomalies/:id`.
  - `pages/AnomalyDetailPage.tsx`: usa `useAnomalyDetail(id)`, muestra
    ficha de detalle completa de la anomalía (`DetailField` × N) —
    **sin** botón/flujo de investigación ni acción de correlación con
    evento más allá de mostrar `correlated_event` como campo de solo
    lectura (eso es SPEC-008).
  - Tests Vitest + Testing Library según sección 5.1/5.2 de este SPEC.
  - Setup de Vitest (`vitest.config.ts` o config dentro de
    `vite.config.ts`, `package.json` script `test`) — primera vez que se
    corren tests de frontend, este SPEC also deja el runner listo.

* **Fuera de Alcance (Out-of-Scope / Non-Goals):**
  - Flujo de "Investigation" (correlacionar anomalía↔evento como acción
    dedicada, CTAs de investigación) — SPEC-008.
  - Editar/resolver/descartar una anomalía (no hay endpoint de backend
    para eso, no se inventa uno).
  - Cualquier gráfico en `AnomaliesPage`/`AnomalyDetailPage` — el único
    gráfico de este SPEC es el histórico de lecturas en `MeterDetailPage`.
  - Paginación de `AnomaliesTable` — mismo criterio que SPEC-006 (dataset
    chico, no pedida, YAGNI).
  - Modificar `api/client.ts`, `api/schemas.ts`, `api/queries/*`,
    `stores/useAnalysisStore.ts`, `router.tsx`, `AppLayout.tsx`,
    `Header.tsx`, `Badge.tsx`, `StatCard.tsx`, `RunAnalysisButton.tsx`,
    `MetersTable.tsx`, `MetersFilterBar.tsx`, `DashboardPage.tsx`,
    `MeterListPage.tsx` — todos ya cerrados, de solo lectura para este
    SPEC.
  - Cualquier cambio en `backend/`.
  - Tocar `specs/TASK_STATUS.md` (ver instrucción 7 arriba).

* **Archivos Afectados:**
  * **Crear:**
    - `frontend/src/components/feature/MeterHistoryChart.tsx`
    - `frontend/src/components/feature/MeterHistoryChart.module.css`
    - `frontend/src/components/feature/AnomaliesTable.tsx`
    - `frontend/src/components/feature/AnomaliesTable.module.css`
    - `frontend/src/components/ui/DetailField.tsx`
    - `frontend/src/components/ui/DetailField.module.css`
    - `frontend/src/components/ui/DetailField.test.tsx`
    - `frontend/src/components/feature/MeterHistoryChart.test.tsx`
    - `frontend/src/components/feature/AnomaliesTable.test.tsx`
    - `frontend/src/pages/MeterDetailPage.test.tsx`
    - `frontend/src/pages/AnomaliesPage.test.tsx`
    - `frontend/src/pages/AnomalyDetailPage.test.tsx`
    - `frontend/src/pages/MeterDetailPage.module.css`
    - `frontend/src/pages/AnomaliesPage.module.css`
    - `frontend/src/pages/AnomalyDetailPage.module.css`
    - `frontend/vitest.config.ts` (o sección `test` dentro de
      `vite.config.ts`, a tu criterio — mientras `pnpm test` funcione)
    - `frontend/src/test/setup.ts` (setup de `@testing-library/jest-dom`)
  * **Modificar:**
    - `frontend/src/pages/MeterDetailPage.tsx` (de placeholder a contenido real)
    - `frontend/src/pages/AnomaliesPage.tsx` (de placeholder a contenido real)
    - `frontend/src/pages/AnomalyDetailPage.tsx` (de placeholder a contenido real)
    - `frontend/package.json` (agregar `echarts`, `echarts-for-react`,
      dependencias de testing de la sección 2, y script `"test": "vitest run"`)
  * **Prohibido modificar:**
    - Todo `backend/**`
    - `readings.csv`, `events.csv`
    - `ARCHITECTURE.md`, `STANDARDS.md`
    - `specs/TASK_STATUS.md`
    - `frontend/src/api/**`, `frontend/src/stores/**`, `frontend/src/router.tsx`
    - `frontend/src/components/layout/**`
    - `frontend/src/components/ui/Badge.tsx`, `StatCard.tsx`, `RunAnalysisButton.tsx` (+ sus `.module.css`)
    - `frontend/src/components/feature/MetersTable.tsx`, `MetersFilterBar.tsx` (+ sus `.module.css`)
    - `frontend/src/pages/DashboardPage.tsx`, `MeterListPage.tsx` (+ sus `.module.css`)

---

## 2. Entorno y Dependencias Permitidas

* **Nuevas dependencias de producción autorizadas:**
  - `echarts` (última estable 5.x)
  - `echarts-for-react` (última estable 3.x)
* **Nuevas dependencias de desarrollo autorizadas:**
  - `vitest`
  - `@testing-library/react`
  - `@testing-library/jest-dom`
  - `@testing-library/user-event`
  - `jsdom`
* Todo lo demás ya instalado en SPEC-005/006 se reutiliza sin cambios.
  Prohibido agregar cualquier otra librería de gráficas, cualquier
  librería de tablas, o Cypress/Playwright (ver `STANDARDS.md` §4.1/§5).

---

## 3. Contratos e Interfaces (Single Source of Truth)

### 3.1 Datos ya disponibles (de SPEC-005, sin cambios)

```typescript
// Ya existen en frontend/src/api/schemas.ts — solo se importan/usan.

interface Reading {
  timestamp: string;       // ISO datetime
  consumption_kwh: number;
  voltage_v: number;
  current_a: number;
  power_factor: number;
  status: string;
}

interface MeterDetailResponse {
  meter_id: string;
  name: string;
  location: string;
  status: string;              // usar meterStatusToColorToken()
  consumption_kwh: number;     // usar formatKwh()
  baseline_kwh: number | null; // usar formatKwh() si no es null
  variation_pct: number | null; // usar formatVariationPct()
  readings: Reading[];
}

interface AnomalySummaryResponse {
  id: string;
  meter_id: string;
  type: string;
  severity: string;             // usar severityToColorToken()
  confidence: number;           // 0-1, formatear como "${(v*100).toFixed(0)}%"
  recommended_action: string;
  detected_at: string;          // usar formatDateTime()
}

interface AnomalyDetailResponse {
  id: string;
  meter_id: string;
  type: string;
  severity: string;
  confidence: number;
  reason: string;
  recommended_action: string;
  baseline_kwh: number;
  observed_kwh: number;
  variation_pct: number;
  affected_variables: string[];
  correlated_event: string | null;
  window_start: string;         // ISO datetime
  window_end: string;           // ISO datetime
}
```

### 3.2 `components/ui/DetailField.tsx` — props

```typescript
interface DetailFieldProps {
  label: string;
  /** Ya formateado por el caller. */
  value: string;
  tone?: "neutral" | "warning" | "critical";
}
export function DetailField(props: DetailFieldProps): JSX.Element { ... }
```

> Igual criterio que `StatCard`/`Badge` de SPEC-006: componente puro,
> nunca decide el mapeo de color, recibe `tone` ya resuelto por el caller
> vía `domain/formatting.ts`.

### 3.3 `components/feature/MeterHistoryChart.tsx` — props y comportamiento

```typescript
type ChartVariable = "consumption_kwh" | "voltage_v" | "current_a" | "power_factor";

interface MeterHistoryChartProps {
  readings: Reading[];
  baselineKwh: number | null;
}
export function MeterHistoryChart(props: MeterHistoryChartProps): JSX.Element { ... }
```

**Comportamiento exacto exigido (implementa el pedido de "selectores
dinámicos para comparar variables"):**

- El componente mantiene **dos selects internos** (estado local
  `useState`), `Serie A` y `Serie B`, cada uno con las 4 opciones de
  `ChartVariable` (etiquetadas en español: "Consumo (kWh)", "Voltaje
  (V)", "Corriente (A)", "Factor de potencia"). Default: `Serie A =
  "consumption_kwh"`, `Serie B = "voltage_v"` (el par más útil para
  detectar tanto `REAL_ANOMALY`/`EXPLAINABLE_ANOMALY` como
  `DATA_QUALITY` a simple vista).
- Un tercer control (checkbox o toggle simple) "Comparar dos variables":
  si está desactivado, se grafica solo `Serie A` (un eje Y). Si está
  activado, se grafican `Serie A` y `Serie B` simultáneamente, cada una
  en su propio eje Y (ECharts `yAxis: [...]` con dos entradas, cada serie
  referenciando su `yAxisIndex`) — así magnitudes muy distintas (kWh vs.
  power_factor 0-1) siguen siendo legibles juntas.
- Eje X siempre es `timestamp` (categoría temporal, ordenado
  cronológicamente tal como viene el array — no reordenar).
- Si `Serie A === "consumption_kwh"` y `baselineKwh !== null`: se agrega
  una tercera serie de tipo línea horizontal constante en `baselineKwh`
  (misma lógica visual que "línea de referencia"), para poder comparar
  consumo real vs. baseline a simple vista — **solo aplica si la serie
  graficada es consumo**, no se agrega baseline como referencia de
  voltaje/corriente/power_factor (no tiene ese significado).
- Colores de las series se toman de `styles/tokens.css` (no la paleta
  default de ECharts) — usa `getComputedStyle(document.documentElement)`
  o variables ya expuestas como constantes TS si `tokens.css` no es
  legible directamente desde JS, a tu criterio, mientras no queden
  colores hardcodeados fuera de los tokens del proyecto.
- Si `readings.length === 0`: renderiza un mensaje simple ("Sin datos
  históricos para este medidor.") en vez de un chart vacío roto.

### 3.4 `components/feature/AnomaliesTable.tsx` — props

```typescript
type AnomalySortableColumn = "meter_id" | "type" | "severity" | "confidence" | "detected_at";

interface AnomaliesTableProps {
  anomalies: AnomalySummaryResponse[];
}
export function AnomaliesTable(props: AnomaliesTableProps): JSX.Element { ... }
```

Mismo patrón exacto que `MetersTable` (SPEC-006, sección 3.5 de ese
SPEC): orden local por columna (click en `<button>` dentro del `<th>`,
cicla asc→desc→sin orden), filas accesibles por teclado
(`role="button"`, `tabIndex={0}`, `onKeyDown` para Enter/Space),
navegación a `/anomalies/{id}` vía `useNavigate()`. Columnas: Medidor
(`meter_id`, texto plano — no hace falta resolver el nombre del medidor,
no hay ese dato en `AnomalySummaryResponse`), Tipo, Severidad (`Badge`
vía `severityToColorToken`), Confianza (formateada como %), Detectada
(`formatDateTime(detected_at)`).

### 3.5 `pages/MeterDetailPage.tsx`

Usa `useMeterDetail(meterId)` (`meterId` desde `useParams()` de
`react-router-dom`, ya autorizado). Mientras `isLoading`: "Cargando…".
Si `isError` o el medidor no existe (CB, ver sección 4.2): mensaje de
error simple. Con datos: ficha de `DetailField` (Nombre, Ubicación,
Estado con `Badge`, Consumo actual, Baseline o "—" si `null`, Variación
o "—" si `null`) + `MeterHistoryChart` recibiendo `readings` y
`baseline_kwh`.

### 3.6 `pages/AnomaliesPage.tsx`

Usa `useAnomalies()`. Mientras `isLoading`: "Cargando…". Si `isError`:
mensaje de error simple. Si `anomalies.length === 0`: "No hay anomalías
detectadas." Con datos: `AnomaliesTable`.

### 3.7 `pages/AnomalyDetailPage.tsx`

Usa `useAnomalyDetail(id)` (`id` desde `useParams()`). Mientras
`isLoading`: "Cargando…". Si `isError` o no existe: mensaje de error
simple. Con datos: ficha de `DetailField` (Medidor `meter_id`, Tipo,
Severidad con `Badge`, Confianza como %, Razón (`reason`, texto largo —
no truncar), Acción recomendada (`recommended_action`), Baseline,
Observado, Variación, Variables afectadas (`affected_variables.join(", ")`
o "—" si array vacío), Evento correlacionado (`correlated_event` o "Sin
evento correlacionado" si `null`), Ventana (`formatDateTime(window_start)`
– `formatDateTime(window_end)`).

---

## 4. Reglas de Negocio y Casos Borde

### 4.1 Reglas de Negocio (RN)

- **RN-01 (Chart nunca recalcula datos):** `MeterHistoryChart` solo
  reordena/selecciona qué series mostrar — nunca calcula un valor nuevo
  (ej. nunca recalcula variación % o promedios) a partir de `readings`.
  Toda cifra derivada ya viene del backend (`baseline_kwh`,
  `variation_pct`) — mismo principio ya fijado en `STANDARDS.md` §4.1
  ("sin lógica de negocio duplicada del backend").
- **RN-02 (Mismo patrón de tabla que SPEC-006):** `AnomaliesTable` reusa
  exactamente el mismo criterio de accesibilidad/orden que `MetersTable`
  — no se reinventa un patrón distinto para la segunda tabla del
  proyecto.
- **RN-03 (Un solo tema de color para el chart):** ninguna serie de
  ECharts usa un color fuera de la paleta de `styles/tokens.css`.

### 4.2 Casos Borde (CB)

- **CB-01 (`meterId`/`id` de ruta inexistente):** Si `useMeterDetail`/
  `useAnomalyDetail` devuelve error (404 del backend) o `isError`, la
  página muestra el mensaje de error simple ya definido en 3.5/3.7 — sin
  crashear, sin pantalla en blanco.
- **CB-02 (Medidor sin anomalías, `readings` con un solo punto o
  vacío):** `MeterHistoryChart` debe renderizar sin romper con 0, 1, o N
  puntos — un chart de una sola muestra es válido (ECharts lo soporta
  nativamente, no requiere lógica especial más allá de CB del propio
  componente en 3.3).
- **CB-03 (`affected_variables` vacío):** se muestra "—", no un string
  vacío ni un array sin formatear.
- **CB-04 (Ambas series iguales, `Serie A === Serie B` con comparación
  activada):** comportamiento válido, no se previene explícitamente —
  ECharts simplemente grafica dos líneas idénticas superpuestas; no
  amerita lógica adicional de este SPEC.

---

## 5. Plan de Ejecución Secuencial (Atomic Tasks)

- [x] **Paso 1: Setup de Vitest:** Instalar dependencias de testing de la
  sección 2, configurar `vitest.config.ts` (entorno `jsdom`,
  `setupFiles: ["src/test/setup.ts"]`), `src/test/setup.ts` importando
  `@testing-library/jest-dom`, script `"test": "vitest run"` en
  `package.json`. Confirmar que `pnpm test` corre (aunque sea 0 tests
  todavía) antes de continuar.
- [x] **Paso 2: `DetailField`:** Implementar componente + test (renderiza
  label/value, aplica clase de tono correcta).
- [x] **Paso 3: `MeterHistoryChart`:** Instalar `echarts`/
  `echarts-for-react`. Implementar según sección 3.3. Tests: renderiza
  sin crashear con 0/1/N readings (CB-02), cambia de serie única a
  comparación al togglear el checkbox, agrega línea de baseline solo
  cuando `Serie A === "consumption_kwh"` y `baselineKwh !== null`.
- [x] **Paso 4: `MeterDetailPage`:** Reemplazar el placeholder, cablear
  `useMeterDetail` + `DetailField` × N + `MeterHistoryChart` (sección
  3.5). Test: smoke test de los 4 estados (loading/error/con datos/
  baseline null).
- [x] **Paso 5: `AnomaliesTable`:** Implementar según sección 3.4 (mismo
  patrón que `MetersTable`). Test: orden cíclico por columna, navegación
  al click/Enter/Space.
- [x] **Paso 6: `AnomaliesPage`:** Reemplazar el placeholder (sección
  3.6). Test: smoke test de los 3 estados (loading/error/vacío/con datos).
- [x] **Paso 7: `AnomalyDetailPage`:** Reemplazar el placeholder (sección
  3.7), incluyendo CB-03. Test: smoke test de los estados + CB-03.
- [x] **Paso 8: Validación:** `pnpm build`, `pnpm lint`, `pnpm test` en
  verde, confirmado independientemente por los arquitectos (retrabajo
  #1: bug de escala en `variation_pct`, ver `TASK_STATUS.md`).
  Verificación visual manual confirmada el 2026-09-25 contra el backend
  real corriendo — reveló un bug real de `yAxis.name` superpuesto en
  `MeterHistoryChart`, corregido en SPEC-009 (no en este SPEC, ya
  cerrado y aprobado antes de esa verificación).

---

## 6. Verificación y Checklist de Salida (Pipeline de 5 Pasos)

- [x] **1. Validación Arquitectónica:**
  - `components/ui/DetailField.tsx` no importa nada de `api/` ni `stores/`.
  - `components/feature/MeterHistoryChart.tsx` y `AnomaliesTable.tsx` no
    hacen fetch propio — reciben todo por props desde las páginas.
  - Ningún archivo de `api/`, `stores/`, `router.tsx`, `AppLayout.tsx`,
    `Header.tsx`, ni los componentes/páginas de SPEC-006 protegidos en la
    sección 1 fue modificado — confirmado.
  - `specs/TASK_STATUS.md` no fue tocado — confirmado en ambas entregas.
  - `git diff` coincidió únicamente con los archivos autorizados en la
    Sección 1. Cero archivos de `backend/` tocados.
- [x] **2. Generación de Tests:**
  - Suite de Vitest + Testing Library presente para los 6 archivos
    listados en la sección 1 (`DetailField`, `MeterHistoryChart`,
    `AnomaliesTable`, y las 3 páginas) — 18/18 tests, primera cobertura
    automatizada del frontend, confirmada independientemente.
- [x] **3. Validación de Cobertura:**
  - `pnpm build`, `pnpm lint`, `pnpm test` en verde — confirmado
    independientemente en ambas rondas.
- [x] **4. Documentación As-Built:**
  - Comentarios JSDoc breves presentes en los props de cada componente
    nuevo — confirmado.
- [x] **5. Trazabilidad y Estado:**
  - Checklist de este SPEC completado. Entrada registrada en
    `specs/TASK_STATUS.md` por los arquitectos (1 ronda de retrabajo
    documentada).
