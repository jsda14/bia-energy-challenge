# SPEC: SPEC-005 - Frontend: Fundación (Setup, Cliente HTTP, Diseño Base, Layout)

> **Instrucciones para el Agente Codificador:**
> 1. No instales dependencias externas, librerías ni paquetes que no estén explícitamente autorizados en la sección 2.
> 2. No agregues campos adicionales, métodos auxiliares públicos ni endpoints fuera de los contratos descritos en la sección 3.
> 3. Implementa únicamente las tareas listadas en la sección 5 en orden secuencial. Si encuentras un bloqueo, detén la ejecución y solicita aclaración.
> 4. Sigue el **Protocolo de Fronteras de STANDARDS.md sección 2** sin excepción: antes de tocar cualquier archivo, cotéjalo contra la sección 1 de este SPEC; antes de escribir cualquier firma/schema, cotéjalo contra la sección 3. Si algo no encaja, emite `BLOCKED_BY_BOUNDARY: <archivo/firma> — <razón>` y detente.
> 5. Este SPEC NO incluye ninguna página de negocio (Dashboard, Meters, Anomalies, Investigation) — esas son SPEC-006 a SPEC-008. Este SPEC es 100% fundación: el proyecto debe levantar, mostrar un layout vacío con navegación funcional, y tener el cliente HTTP + stores listos para que los SPECs siguientes solo agreguen páginas.
> 6. **No modifiques nada de `backend/`** — este SPEC es exclusivamente frontend. Los contratos de la API (sección 3.1) son de solo lectura, ya cerrados en SPEC-003.

---

## 1. Alcance y Fronteras

* **Objetivo:** Inicializar el proyecto frontend (Vite + React + TypeScript
  + pnpm), con la arquitectura por capas de `ARCHITECTURE.md` §7.1 lista
  (`domain/`, `api/`, `stores/`, `components/`, `pages/`), el cliente HTTP
  tipado con Zod contra los 6 endpoints reales del backend, los tokens de
  diseño base, el layout de aplicación (header + navegación) con routing
  funcional entre 5 rutas placeholder, y el store de Zustand para el estado
  de "análisis en curso".

* **En Alcance (In-Scope):**
  - Setup de proyecto: `pnpm create vite` (template `react-ts`), estructura
    de carpetas de `ARCHITECTURE.md` §3/§7.1.
  - `api/client.ts`: cliente `fetch` base (base URL configurable, manejo de
    errores HTTP no-2xx).
  - `api/schemas.ts`: schemas Zod para las 6 respuestas reales del backend
    (sección 3.1).
  - `api/queries/`: un hook de TanStack Query por endpoint (6 hooks),
    parseando cada respuesta con su schema Zod.
  - `domain/types.ts`: tipos inferidos de los schemas Zod (`z.infer`).
  - `domain/formatting.ts`: funciones puras de formateo (sección 3.3).
  - `stores/useAnalysisStore.ts`: store de Zustand para el estado de
    análisis en curso (sección 3.4).
  - `styles/tokens.css`: paleta, espaciado, tipografía, radios, sombras,
    variables de breakpoint (los 8 de `STANDARDS.md` §4.4).
  - `styles/reset.css`: reset mínimo cross-browser.
  - Layout de aplicación: header con nombre "Bia Energy" + navegación (5
    links: Dashboard, Medidores, Anomalías — Detalle/Investigación se
    navegan desde dentro de esas páginas, no desde el nav principal).
  - `router.tsx`: 5 rutas registradas
    (`/`, `/meters`, `/meters/:meterId`, `/anomalies`, `/anomalies/:id`),
    cada una renderizando un componente placeholder mínimo (un `<h1>` con
    el nombre de la página) — el contenido real de cada página es
    SPEC-006/007/008.
  - Indicador no bloqueante de "análisis en curso" en el header (lee de
    `useAnalysisStore`).
  - `.env.example` con `VITE_API_BASE_URL`.

* **Fuera de Alcance (Out-of-Scope / Non-Goals):**
  - Contenido real de cualquier página (KPIs, tablas, gráficas, formularios)
    — SPEC-006, SPEC-007, SPEC-008.
  - Componentes de `components/ui/` más allá de lo estrictamente necesario
    para el layout (un `Header`, un `NavLink`) — el resto de componentes
    genéricos (`Button`, `Badge`, `Card`, `Table`) se crean cuando la
    página que los necesita los requiera, no antes (YAGNI).
  - Lógica real de disparo de `POST /ai/analyze` (el botón "Run AI
    Analysis" vive en el Dashboard — SPEC-006). Este SPEC solo deja listo
    el store que ese botón va a usar.
  - Tests con Vitest/Testing Library de componentes de negocio — no hay
    componentes de negocio todavía. Si acaso, un test mínimo de que el
    router monta sin errores.
  - Cualquier cambio en `backend/`.

* **Archivos Afectados:**
  * **Crear:**
    - `frontend/package.json`
    - `frontend/pnpm-lock.yaml` (generado por `pnpm install`, no escrito a mano)
    - `frontend/tsconfig.json`
    - `frontend/vite.config.ts`
    - `frontend/index.html`
    - `frontend/.env.example`
    - `frontend/.gitignore` (si no existe ya uno raíz que cubra `frontend/node_modules`, `frontend/dist`)
    - `frontend/src/main.tsx`
    - `frontend/src/router.tsx`
    - `frontend/src/domain/types.ts`
    - `frontend/src/domain/formatting.ts`
    - `frontend/src/api/client.ts`
    - `frontend/src/api/schemas.ts`
    - `frontend/src/api/queries/useDashboardSummary.ts`
    - `frontend/src/api/queries/useMeters.ts`
    - `frontend/src/api/queries/useMeterDetail.ts`
    - `frontend/src/api/queries/useAnomalies.ts`
    - `frontend/src/api/queries/useAnomalyDetail.ts`
    - `frontend/src/api/queries/useRunAnalysis.ts`
    - `frontend/src/stores/useAnalysisStore.ts`
    - `frontend/src/styles/tokens.css`
    - `frontend/src/styles/reset.css`
    - `frontend/src/components/layout/AppLayout.tsx`
    - `frontend/src/components/layout/AppLayout.module.css`
    - `frontend/src/components/layout/Header.tsx`
    - `frontend/src/components/layout/Header.module.css`
    - `frontend/src/pages/DashboardPage.tsx` (placeholder mínimo)
    - `frontend/src/pages/MeterListPage.tsx` (placeholder mínimo)
    - `frontend/src/pages/MeterDetailPage.tsx` (placeholder mínimo)
    - `frontend/src/pages/AnomaliesPage.tsx` (placeholder mínimo)
    - `frontend/src/pages/AnomalyDetailPage.tsx` (placeholder mínimo)
  * **Modificar:**
    - Ninguno (proyecto frontend nuevo, todo es creación).
  * **Prohibido modificar:**
    - Todo `backend/**`
    - `readings.csv`, `events.csv`
    - `ARCHITECTURE.md`, `STANDARDS.md`

---

## 2. Entorno y Dependencias Permitidas

* **Runtime / Versión:** Node.js 20+, gestor de paquetes `pnpm` (no `npm`,
  no `yarn` — si `pnpm` no está disponible en el entorno de ejecución,
  detente y repórtalo, no sustituyas por otro gestor).
* **Dependencias de producción autorizadas:**
  - `react`, `react-dom` (últimas versiones estables 18.x)
  - `react-router-dom` (v6.x)
  - `@tanstack/react-query` (v5.x)
  - `zustand` (v4.x o v5.x)
  - `zod` (v3.x)
* **Dependencias de desarrollo autorizadas:**
  - `vite`, `@vitejs/plugin-react`
  - `typescript`
  - `@types/react`, `@types/react-dom`
  - `eslint` + config razonable de React/TypeScript (si Vite la trae por
    defecto con el template `react-ts`, úsala; no agregues un setup de
    lint elaborado no pedido)
* **Regla estricta:** Prohibido Tailwind, cualquier librería de
  componentes UI (MUI, Chakra, Ant Design, shadcn/ui, etc.), Redux/Redux
  Toolkit, Axios (usa `fetch` nativo), `openapi-typescript` o cualquier
  generador de tipos desde OpenAPI, cualquier librería de gráficas (eso es
  SPEC-007, cuando haga falta graficar el histórico de un medidor — no se
  anticipa aquí).

---

## 3. Contratos e Interfaces (Single Source of Truth)

### 3.1 Endpoints reales del backend (verificados contra el código de SPEC-003)

```
POST /ai/analyze              body: { meter_id: string | null }  → AnalysisRunResponse
GET  /dashboard/summary                                           → DashboardSummaryResponse
GET  /meters                                                      → MeterSummaryResponse[]
GET  /meters/{meterId}                                            → MeterDetailResponse
GET  /anomalies                                                   → AnomalySummaryResponse[]
GET  /anomalies/{id}                                              → AnomalyDetailResponse
```

> Nota: `MeterDetailResponse` trae `readings` embebido (no existe un
> endpoint separado `GET /meters/:meterId/readings` — el diseño original
> de `ARCHITECTURE.md` §6 sugería uno, pero SPEC-003 lo consolidó dentro
> del detalle). Los schemas de abajo reflejan el backend real, no el
> diseño original.

### 3.2 Schemas Zod (`api/schemas.ts`)

Réplica exacta de `backend/app/adapters/inbound/api/schemas.py`:

```typescript
// frontend/src/api/schemas.ts
import { z } from "zod";

export const analysisRunResponseSchema = z.object({
  id: z.string(),
  requested_meter_id: z.string().nullable(),
  status: z.string(),
  started_at: z.string(), // ISO datetime string; se formatea en domain/formatting.ts, no aquí
  finished_at: z.string(),
  anomalies_detected_count: z.number(),
  error_message: z.string().nullable(),
});

export const dashboardSummaryResponseSchema = z.object({
  anomalies_detected: z.number(),
  high_priority_count: z.number(),
  average_confidence: z.number().nullable(),
  last_analysis_at: z.string().nullable(),
});

export const meterSummaryResponseSchema = z.object({
  meter_id: z.string(),
  name: z.string(),
  status: z.string(),
  consumption_kwh: z.number(),
  variation_pct: z.number().nullable(),
  anomaly_severity: z.string().nullable(),
});

export const readingResponseSchema = z.object({
  timestamp: z.string(),
  consumption_kwh: z.number(),
  voltage_v: z.number(),
  current_a: z.number(),
  power_factor: z.number(),
  status: z.string(),
});

export const meterDetailResponseSchema = z.object({
  meter_id: z.string(),
  name: z.string(),
  location: z.string(),
  status: z.string(),
  consumption_kwh: z.number(),
  baseline_kwh: z.number().nullable(),
  variation_pct: z.number().nullable(),
  readings: z.array(readingResponseSchema),
});

export const anomalySummaryResponseSchema = z.object({
  id: z.string(),
  meter_id: z.string(),
  type: z.string(),
  severity: z.string(),
  confidence: z.number(),
  recommended_action: z.string(),
  detected_at: z.string(),
});

export const anomalyDetailResponseSchema = z.object({
  id: z.string(),
  meter_id: z.string(),
  type: z.string(),
  severity: z.string(),
  confidence: z.number(),
  reason: z.string(),
  recommended_action: z.string(),
  baseline_kwh: z.number(),
  observed_kwh: z.number(),
  variation_pct: z.number(),
  affected_variables: z.array(z.string()),
  correlated_event: z.string().nullable(),
  window_start: z.string(),
  window_end: z.string(),
});
```

> `status`/`type`/`severity` se tipan como `z.string()`, no `z.enum([...])`
> — el backend los serializa como string plano (son `Enum` de Python
> serializados por Pydantic), y fijar un `z.enum` aquí duplicaría el
> conjunto de valores válidos que ya vive en el dominio del backend
> (`AnomalyType`, `Severity`, `AnalysisRunStatus`). Los valores válidos
> conocidos para renderizado (badges de color, etc.) se documentan como
> constantes en `domain/formatting.ts` (sección 3.3), no como validación
> estricta de Zod — si el backend algún día agrega un valor nuevo, el
> frontend no debe romper el parseo, solo no saber cómo colorearlo (con
> un fallback neutro).

### 3.3 `domain/formatting.ts` — firmas exactas

```typescript
// frontend/src/domain/formatting.ts

/** Formatea un valor en kWh con 1 decimal y sufijo, ej. "1,234.5 kWh". */
export function formatKwh(value: number): string { ... }

/** Formatea una variación porcentual con signo, ej. "+78.9%" o "-12.3%". */
export function formatVariationPct(value: number): string { ... }

/** Formatea un ISO datetime string a fecha/hora legible en es-ES, ej.
 * "24 sep 2026, 14:00". */
export function formatDateTime(isoString: string): string { ... }

/** Mapea un severity string del backend ("LOW"|"MEDIUM"|"HIGH") a un
 * token de color semántico ("neutral"|"warning"|"critical"). Cualquier
 * valor no reconocido retorna "neutral" (fallback seguro, nunca lanza). */
export function severityToColorToken(severity: string): "neutral" | "warning" | "critical" { ... }

/** Mapea un meter status string ("OK"|"Alert"|"Critical") a un token de
 * color semántico, mismo criterio de fallback que severityToColorToken. */
export function meterStatusToColorToken(status: string): "neutral" | "warning" | "critical" { ... }
```

### 3.4 `stores/useAnalysisStore.ts`

```typescript
// frontend/src/stores/useAnalysisStore.ts
import { create } from "zustand";

interface AnalysisState {
  isRunning: boolean;
  lastRunId: string | null;
  /** Marca el inicio de un análisis (antes de llamar a la mutación). */
  startRun: () => void;
  /** Marca el fin de un análisis, exitoso o no — el caller decide si
   * invalidar queries de TanStack Query por fuera de este store (el
   * store NO conoce TanStack Query, solo expone su propio estado). */
  finishRun: (runId: string) => void;
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  isRunning: false,
  lastRunId: null,
  startRun: () => set({ isRunning: true }),
  finishRun: (runId: string) => set({ isRunning: false, lastRunId: runId }),
}));
```

> Este store NO dispara la llamada HTTP — eso lo hace el hook
> `useRunAnalysis` (sección 3.5), que internamente llama
> `startRun()`/`finishRun()` alrededor de su mutación. El store es puro
> estado, sin lógica de red.

### 3.5 Hooks de `api/queries/` — firmas

```typescript
// frontend/src/api/queries/useDashboardSummary.ts
export function useDashboardSummary() {
  // usa useQuery de TanStack Query, queryKey: ["dashboard-summary"],
  // fetch a GET /dashboard/summary, parsea con dashboardSummaryResponseSchema
}

// frontend/src/api/queries/useMeters.ts
export function useMeters() {
  // queryKey: ["meters"], GET /meters, parsea con z.array(meterSummaryResponseSchema)
}

// frontend/src/api/queries/useMeterDetail.ts
export function useMeterDetail(meterId: string) {
  // queryKey: ["meters", meterId], GET /meters/{meterId},
  // parsea con meterDetailResponseSchema. enabled: !!meterId
}

// frontend/src/api/queries/useAnomalies.ts
export function useAnomalies() {
  // queryKey: ["anomalies"], GET /anomalies, parsea con z.array(anomalySummaryResponseSchema)
}

// frontend/src/api/queries/useAnomalyDetail.ts
export function useAnomalyDetail(anomalyId: string) {
  // queryKey: ["anomalies", anomalyId], GET /anomalies/{id},
  // parsea con anomalyDetailResponseSchema. enabled: !!anomalyId
}

// frontend/src/api/queries/useRunAnalysis.ts
export function useRunAnalysis() {
  // usa useMutation de TanStack Query. mutationFn: POST /ai/analyze con
  // body { meter_id }, parsea con analysisRunResponseSchema. Al iniciar
  // (onMutate) llama useAnalysisStore.getState().startRun(); al
  // completar (onSuccess/onSettled) llama
  // useAnalysisStore.getState().finishRun(result.id) e invalida las
  // queryKeys ["dashboard-summary"], ["meters"], ["anomalies"] para que
  // se refresquen solas.
}
```

### 3.6 Layout y routing

```typescript
// frontend/src/router.tsx — estructura de rutas (usa createBrowserRouter
// o <Routes> declarativo, a tu criterio, mientras las 5 rutas existan
// exactamente así):
// "/"                    → DashboardPage
// "/meters"              → MeterListPage
// "/meters/:meterId"     → MeterDetailPage
// "/anomalies"           → AnomaliesPage
// "/anomalies/:id"       → AnomalyDetailPage
// Todas envueltas por AppLayout (header + nav + <Outlet/>).
```

`Header.tsx` muestra: nombre "Bia Energy", nav con 3 links (Dashboard,
Medidores → `/meters`, Anomalías → `/anomalies`), y un indicador visual no
bloqueante que lee `useAnalysisStore().isRunning` (ej. un pequeño spinner o
badge "Analizando…" — implementación visual simple, el contenido rico del
indicador se puede refinar en SPEC-006 si hace falta, este SPEC solo
requiere que el indicador EXISTA y reaccione al store).

---

## 4. Reglas de Negocio y Casos Borde

### 4.1 Reglas de Negocio (RN)

- **RN-01 (Parseo estricto):** Todo hook de `api/queries/` parsea la
  respuesta HTTP con su schema Zod antes de retornar datos. Si el parseo
  falla (`ZodError`), el hook debe propagar el error de forma que
  TanStack Query lo capture como estado de error (no debe silenciarse ni
  devolver `null`/datos parciales).
- **RN-02 (Cliente HTTP centralizado):** Ningún hook de `api/queries/`
  usa `fetch` directamente — todos pasan por `api/client.ts`, que centraliza
  la base URL (`import.meta.env.VITE_API_BASE_URL`) y el manejo de
  respuestas no-2xx (lanza un error con el status code y el body, si lo
  hay, para que TanStack Query lo capture).
- **RN-03 (Invalidación tras análisis):** `useRunAnalysis` invalida
  exactamente las 3 queryKeys mencionadas en la sección 3.5 tras
  completarse (éxito o error) — no invalida `["meters", meterId]` de
  detalles individuales (eso se refresca solo si el usuario vuelve a
  entrar a esa página, no hace falta invalidar cada detalle posible).
- **RN-04 (Mobile-first real):** El layout (`AppLayout`, `Header`) se
  construye mobile-first según `STANDARDS.md` §4.4 — en viewport `xs`
  (480px) el nav puede colapsar a un menú compacto si el ancho no alcanza
  para los 3 links + nombre + indicador de análisis; a partir de `md`
  (768px) se muestra expandido. No hace falta un menú hamburguesa
  elaborado — con que el header no rompa el layout ni desborde
  horizontalmente en 320-480px es suficiente para este SPEC.

### 4.2 Casos Borde (CB)

- **CB-01 (Backend no disponible):** Si el backend no responde (error de
  red, `fetch` rechaza la promesa), el hook correspondiente de TanStack
  Query debe exponer `isError: true` — no debe colgar la UI ni lanzar una
  excepción no capturada en el árbol de React. Este SPEC no requiere una
  UI de error elaborada por página (eso es de cada SPEC de página
  específico), pero el mecanismo de propagación de error debe funcionar.
- **CB-02 (Análisis disparado dos veces seguidas):** Si `useRunAnalysis`
  se invoca mientras `isRunning` ya es `true`, no hay protección explícita
  en este SPEC contra doble-click (eso es responsabilidad visual del botón
  en SPEC-006, que puede deshabilitarse mientras `isRunning`) — el store en
  sí no bloquea llamadas concurrentes, solo refleja el último estado.
- **CB-03 (Ruta con `meterId`/`id` inexistente):** Las páginas placeholder
  de este SPEC no necesitan manejar el caso de un id inexistente (eso es
  SPEC-007/008, cuando la página tenga contenido real que dependa del
  dato) — solo deben renderizar sin crashear si el parámetro de ruta no
  corresponde a nada real.

---

## 5. Plan de Ejecución Secuencial (Atomic Tasks)

- [x] **Paso 1: Setup del proyecto:** `pnpm create vite frontend -- --template react-ts`
  (o equivalente), configurar `tsconfig.json` con `strict: true`. Instalar
  las dependencias de la sección 2. Confirmar que `pnpm dev` levanta el
  proyecto base sin errores antes de continuar.
- [x] **Paso 2: Tokens y reset de estilos:** Crear `styles/tokens.css` (
  paleta, espaciado, tipografía, radios, sombras, y las 8 variables de
  breakpoint de `STANDARDS.md` §4.4) y `styles/reset.css`. Importarlos en
  `main.tsx`.
- [x] **Paso 3: Capa `domain/`:** Implementar `types.ts` (re-exports de los
  tipos inferidos de Zod) y `formatting.ts` según sección 3.3.
- [x] **Paso 4: Capa `api/`:** Implementar `schemas.ts` (sección 3.2),
  `client.ts` (RN-02), y los 6 hooks de `queries/` (sección 3.5),
  cumpliendo RN-01, RN-03, CB-01.
- [x] **Paso 5: Store de Zustand:** Implementar `stores/useAnalysisStore.ts`
  según sección 3.4.
- [x] **Paso 6: Layout:** Implementar `AppLayout`, `Header` (BEM + CSS
  Modules, mobile-first según RN-04), y `router.tsx` con las 5 rutas y sus
  páginas placeholder (un `<h1>` con el nombre de cada página, nada más).
- [x] **Paso 7: Validación:** `pnpm build` confirmado sin errores de
  TypeScript, corrido de forma independiente por los arquitectos (no solo
  confiando en el reporte del agente). Verificación visual manual de las 5
  rutas y responsive en 2 viewports no se pudo confirmar en el entorno
  sandboxed de auditoría (limitación del entorno, no del código) — queda
  pendiente de verificación visual manual por el usuario antes de la demo.

---

## 6. Verificación y Checklist de Salida (Pipeline de 5 Pasos)

- [x] **1. Validación Arquitectónica:**
  - `domain/` no importa nada de `api/`, `stores/`, `components/` ni
    `pages/` — **excepción menor**: `domain/types.ts` importa tipos (no
    runtime) desde `api/schemas.ts` para re-exportarlos vía `z.infer`;
    TypeScript borra esto en compilación, sin acoplamiento real en el
    bundle. Aceptado como parte natural del patrón "tipos inferidos de
    Zod" que el propio SPEC pidió.
  - `components/` no importa nada de `api/` ni `stores/` directamente —
    **excepción documentada**: `Header.tsx` sí importa `useAnalysisStore`
    directamente, tal como la propia sección 3.6 de este SPEC lo
    especificaba (contradicción entre esa sección y la regla general de
    `ARCHITECTURE.md` §7.1, detectada en auditoría — error de diseño del
    SPEC, no de la implementación). Documentado como excepción puntual en
    `ARCHITECTURE.md` §7.1; no aplica a componentes futuros.
  - Ningún archivo usa Tailwind, una librería de componentes UI, Redux, ni
    Axios — confirmado.
  - `git diff` coincide únicamente con los archivos autorizados en la
    Sección 1 tras el retrabajo #1. Cero archivos de `backend/` tocados.
- [x] **2. Generación de Tests:**
  - No aplica cobertura de tests de negocio en este SPEC (no hay lógica de
    negocio todavía) — se retoma en SPEC-006 en adelante.
- [x] **3. Validación de Cobertura:**
  - `pnpm build` compila sin errores de TypeScript (`strict: true`
    respetado en todo el código nuevo) — confirmado independientemente.
    `pnpm lint` (eslint, tras retrabajo #1) también en verde.
- [x] **4. Documentación As-Built:**
  - Comentarios JSDoc en las funciones de `domain/formatting.ts`.
- [x] **5. Trazabilidad y Estado:**
  - Checklist de este SPEC completado y entrada registrada en
    `specs/TASK_STATUS.md` (1 ronda de retrabajo documentada).
