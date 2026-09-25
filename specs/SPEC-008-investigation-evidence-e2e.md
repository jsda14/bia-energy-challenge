# SPEC: SPEC-008 - Frontend: Evidencia Visual de Investigación y E2E

> **Instrucciones para el Agente Codificador:**
> 1. No instales dependencias externas, librerías ni paquetes que no estén explícitamente autorizados en la sección 2.
> 2. No agregues campos adicionales, métodos auxiliares públicos ni endpoints fuera de los contratos descritos en la sección 3.
> 3. Implementa únicamente las tareas listadas en la sección 5 en orden secuencial. Si encuentras un bloqueo, detén la ejecución y solicita aclaración.
> 4. Sigue el **Protocolo de Fronteras de STANDARDS.md sección 2** sin excepción: antes de tocar cualquier archivo, cotéjalo contra la sección 1 de este SPEC; antes de escribir cualquier firma/prop, cotéjalo contra la sección 3. Si algo no encaja, emite `BLOCKED_BY_BOUNDARY: <archivo/firma> — <razón>` y detente.
> 5. **Este SPEC NO crea una página ni ruta nueva de "Investigation".** Según `ARCHITECTURE.md` §7, el flujo de investigación (evidencia, variables afectadas, evento correlacionado, severidad/confianza, acción recomendada) ya está cubierto por `AnomalyDetailPage` (SPEC-007). Lo único que faltaba explícitamente de esa sección del PDF es "evidencia (gráfica con la ventana anómala resaltada)" — eso es el alcance real de este SPEC. No dupliques UI ya construida.
> 6. Este SPEC modifica `MeterHistoryChart.tsx` (cerrado en SPEC-007) de forma **aditiva y opcional** (props nuevas con default que preservan el comportamiento actual) — no rompas ningún uso existente del componente en `MeterDetailPage`.
> 7. **Este SPEC exige tests automatizados** (Vitest + Testing Library) según `STANDARDS.md` §5, incluyendo el primer test E2E de navegación del proyecto (sección 5.2 de este documento).
> 8. **`specs/TASK_STATUS.md` NO se toca** — misma instrucción que SPEC-007, que funcionó correctamente. Si necesitás notas internas, usá algo fuera del repositorio.
> 9. **No modifiques nada de `backend/`** — este SPEC es exclusivamente frontend.

---

## 1. Alcance y Fronteras

* **Objetivo:** Cerrar el flujo de investigación del PDF agregando
  resaltado visual de la ventana anómala (`window_start`–`window_end`)
  al gráfico histórico ya existente, mostrado en `AnomalyDetailPage`, y
  cerrar el proyecto con una suite de tests E2E de navegación entre las
  5 rutas del frontend.

* **En Alcance (In-Scope):**
  - Extender `components/feature/MeterHistoryChart.tsx` (SPEC-007) con
    dos props nuevas y opcionales para resaltar una ventana temporal
    (`highlightStart`/`highlightEnd`) — ver contrato exacto en sección 3.1.
  - `pages/AnomalyDetailPage.tsx`: agregar el fetch de
    `useMeterDetail(anomaly.meter_id)` (ya existe el hook, de SPEC-005)
    para obtener `readings`/`baseline_kwh` del medidor de la anomalía, y
    renderizar `MeterHistoryChart` con la ventana resaltada.
  - `frontend/src/e2e/navigation.test.tsx`: primer test E2E del
    proyecto, navegación real entre las 5 rutas usando
    `<RouterProvider>` completo (no mocks de router).
  - Tests unitarios de la extensión de `MeterHistoryChart` (highlight).

* **Fuera de Alcance (Out-of-Scope / Non-Goals):**
  - Cualquier página o ruta nueva — no se crea `/investigation` ni
    similar (ver instrucción 5).
  - Cualquier acción de "resolver"/"descartar" una anomalía — no hay
    endpoint de backend para eso.
  - Playwright o cualquier runner E2E de navegador real — descartado
    explícitamente en `STANDARDS.md` §5, se mantiene esa decisión.
  - Cambios en `MeterDetailPage.tsx` más allá de lo estrictamente
    necesario para que siga funcionando igual con las nuevas props
    opcionales de `MeterHistoryChart` (no debería requerir ningún
    cambio, ya que las props nuevas son opcionales).
  - Modificar `api/`, `stores/`, `router.tsx`, `AppLayout.tsx`,
    `Header.tsx`, cualquier componente de SPEC-005/006, ni
    `AnomaliesPage.tsx`/`AnomaliesTable.tsx` (sin cambios de alcance
    para ellos en este SPEC).
  - Cualquier cambio en `backend/`.
  - Tocar `specs/TASK_STATUS.md`.

* **Archivos Afectados:**
  * **Crear:**
    - `frontend/src/e2e/navigation.test.tsx`
    - `frontend/src/e2e/` (directorio nuevo, primera vez que se separan
      tests E2E de tests unitarios/de componente)
  * **Modificar:**
    - `frontend/src/components/feature/MeterHistoryChart.tsx` (props
      nuevas y opcionales, sección 3.1)
    - `frontend/src/components/feature/MeterHistoryChart.test.tsx`
      (tests nuevos para el highlight, agregados a la suite existente)
    - `frontend/src/pages/AnomalyDetailPage.tsx` (agregar
      `useMeterDetail` + renderizar el chart)
    - `frontend/src/pages/AnomalyDetailPage.test.tsx` (test nuevo para
      la sección de evidencia visual)
  * **Prohibido modificar:**
    - Todo `backend/**`
    - `readings.csv`, `events.csv`
    - `ARCHITECTURE.md`, `STANDARDS.md`
    - `specs/TASK_STATUS.md`
    - `frontend/src/api/**`, `frontend/src/stores/**`, `frontend/src/router.tsx`
    - `frontend/src/components/layout/**`
    - `frontend/src/components/ui/**` (Badge, StatCard, RunAnalysisButton, DetailField)
    - `frontend/src/components/feature/MetersTable.tsx`,
      `MetersFilterBar.tsx`, `AnomaliesTable.tsx`, `chartColors.ts`
    - `frontend/src/pages/DashboardPage.tsx`, `MeterListPage.tsx`,
      `MeterDetailPage.tsx`, `AnomaliesPage.tsx` (contenido — solo
      `AnomalyDetailPage.tsx` se modifica en este SPEC)

---

## 2. Entorno y Dependencias Permitidas

* Ninguna dependencia nueva. Se reutiliza exactamente lo instalado en
  SPEC-005/006/007 (`echarts`, `echarts-for-react`, `vitest`,
  `@testing-library/react`, `@testing-library/jest-dom`,
  `@testing-library/user-event`, `jsdom`). El test E2E se escribe con
  las mismas herramientas ya instaladas — Testing Library soporta
  perfectamente un smoke test de navegación completo sin necesitar
  Playwright/Cypress (explícitamente descartados en `STANDARDS.md` §5).

---

## 3. Contratos e Interfaces (Single Source of Truth)

### 3.1 `components/feature/MeterHistoryChart.tsx` — extensión de props

```typescript
// Firma ANTERIOR (SPEC-007, sin cambios en su comportamiento por defecto):
interface MeterHistoryChartProps {
  readings: Reading[];
  baselineKwh: number | null;
  /** NUEVO — opcional. Si ambos vienen definidos, se resalta esa ventana
   * temporal sobre el gráfico con una banda vertical semitransparente
   * (ECharts `markArea`). Si se omite cualquiera de los dos, el
   * comportamiento es idéntico al de SPEC-007 (sin resaltado). */
  highlightStart?: string; // ISO datetime, igual formato que Reading.timestamp
  highlightEnd?: string;   // ISO datetime
}
```

**Implementación exacta exigida:**
- Cuando `highlightStart` y `highlightEnd` están ambos definidos, se
  agrega una entrada `markArea` a la serie de `Serie A` (la primera
  serie, ya existente) con `data: [[{ xAxis: highlightStart }, { xAxis:
  highlightEnd }]]`, usando un color semitransparente derivado de
  `CHART_COLOR_BASELINE` de `chartColors.ts` (ej. mismo hex con
  `opacity`/`rgba` reducida vía la opción `itemStyle.color` de ECharts
  con canal alpha, ej. `"rgba(114, 34, 36, 0.15)"` — deriválo del mismo
  hex ya definido, no inventes un color nuevo).
- Este `markArea` aplica **siempre**, sin importar qué variable esté
  seleccionada en `Serie A` (a diferencia del `markLine` de baseline,
  que solo aplica cuando `Serie A === "consumption_kwh"`) — la ventana
  anómala es relevante para cualquier variable que se esté mirando
  (ej. en un caso `DATA_QUALITY` como M-112, el usuario probablemente
  quiere ver la ventana resaltada mientras mira voltaje/power_factor,
  no consumo).
- Sin `highlightStart`/`highlightEnd`: comportamiento idéntico al
  componente de SPEC-007, sin ningún cambio visual.

### 3.2 `pages/AnomalyDetailPage.tsx` — cambio de composición

Se agrega, después de la sección de `DetailField` existente (sin
modificar nada de lo ya aprobado en SPEC-007) y antes de las secciones
de "Razón"/"Acción Recomendada":

```typescript
// Nuevo en este SPEC:
const { data: meter, isLoading: isMeterLoading } = useMeterDetail(anomaly?.meter_id ?? "");
```

- Se llama `useMeterDetail` con `enabled: !!anomaly?.meter_id` (ya es el
  comportamiento del hook, definido en SPEC-005 — no hace falta lógica
  extra, simplemente pasarle el id disponible recién cuando
  `anomaly` ya cargó).
- Nueva sección "Evidencia Visual" (`<h2>` + el chart), renderizada solo
  cuando `meter` (el `MeterDetailResponse`) está disponible. Mientras
  `isMeterLoading`, esa sección muestra "Cargando evidencia visual…" —
  el resto de la página (ficha de `DetailField`, razón, acción
  recomendada) se renderiza igual que en SPEC-007, sin esperar al
  medidor.
- `MeterHistoryChart` recibe `readings={meter.readings}`,
  `baselineKwh={meter.baseline_kwh}`, `highlightStart={anomaly.window_start}`,
  `highlightEnd={anomaly.window_end}`.
- Si `useMeterDetail` da error (CB, ver sección 4.2): la sección de
  evidencia visual muestra un mensaje de error simple, sin afectar el
  resto de la página (que ya tiene sus propios datos de `anomaly`).

### 3.3 `e2e/navigation.test.tsx` — smoke test de navegación

Requisitos exactos:
- Monta la app completa (mismo `router.tsx`/`AppLayout` reales, no
  mocks) dentro de un `QueryClientProvider` de test (mismo patrón ya
  usado en los tests de páginas de SPEC-007 — revisar cómo lo resuelven
  antes de escribir este archivo, para reusar el mismo helper si ya
  existe, o crear uno común en `src/test/` si conviene, a tu criterio,
  mientras no dupliques 5 veces el mismo boilerplate).
- Mockea las respuestas HTTP necesarias (`api/client.ts` o `fetch`
  global, a tu criterio) con datos mínimos realistas: al menos 1
  medidor, 1 anomalía, con IDs que permitan navegar a sus rutas de
  detalle.
- Test 1: desde `/` (Dashboard), hace click en el link de navegación a
  "Medidores" (Header, ya existe de SPEC-005) y verifica que la URL/el
  contenido corresponde a `MeterListPage`.
- Test 2: desde `MeterListPage`, hace click en una fila de la tabla y
  verifica que navega a `MeterDetailPage` con el `meterId` correcto en
  la URL.
- Test 3: desde el Header, navega a "Anomalías" y verifica
  `AnomaliesPage`; hace click en una fila y verifica que navega a
  `AnomalyDetailPage` con el `id` correcto.
- No hace falta cubrir todas las combinaciones posibles — el objetivo es
  probar que el router real conecta las 5 páginas reales entre sí, no
  repetir la cobertura unitaria que ya existe por componente/página
  desde SPEC-007.

---

## 4. Reglas de Negocio y Casos Borde

### 4.1 Reglas de Negocio (RN)

- **RN-01 (Highlight nunca reemplaza el baseline):** si `Serie A ===
  "consumption_kwh"`, `baselineKwh !== null`, y además hay
  `highlightStart`/`highlightEnd`, ambos (`markLine` de baseline y
  `markArea` de ventana) coexisten en la misma serie — no son
  mutuamente excluyentes.
- **RN-02 (`AnomalyDetailPage` sigue funcionando si el fetch del
  medidor falla):** la ficha de datos de la anomalía (ya aprobada en
  SPEC-007) nunca depende del resultado de `useMeterDetail` — son dos
  queries independientes, un fallo en una no debe ocultar la otra.

### 4.2 Casos Borde (CB)

- **CB-01 (Medidor de la anomalía no existe o da error):** la sección
  "Evidencia Visual" muestra su propio mensaje de error, el resto de
  `AnomalyDetailPage` (ficha, razón, acción recomendada) se renderiza
  normalmente con los datos de `anomaly` que sí cargaron.
- **CB-02 (Ventana de la anomalía fuera del rango de `readings` del
  medidor):** no debería ocurrir con los datos reales del dataset
  (la ventana siempre es un subconjunto del histórico), pero si pasara,
  ECharts simplemente no dibuja el `markArea` fuera del rango visible
  del eje X — no requiere manejo especial de este SPEC.
- **CB-03 (Test E2E con backend real no disponible):** los tests E2E de
  este SPEC corren con `fetch`/`api/client` mockeado (no contra un
  servidor real) — no dependen de que el backend esté corriendo, mismo
  criterio que todos los tests de frontend desde SPEC-007.

---

## 5. Plan de Ejecución Secuencial (Atomic Tasks)

- [ ] **Paso 1: Extender `MeterHistoryChart`:** Agregar
  `highlightStart`/`highlightEnd` opcionales según sección 3.1. Tests
  nuevos en `MeterHistoryChart.test.tsx`: con highlight, sin highlight
  (comportamiento idéntico a SPEC-007), highlight coexistiendo con
  baseline. Confirmar que los tests YA EXISTENTES de SPEC-007 en este
  mismo archivo siguen pasando sin modificarlos (backward-compatible).
- [ ] **Paso 2: `AnomalyDetailPage` — evidencia visual:** Agregar
  `useMeterDetail` + sección "Evidencia Visual" según sección 3.2. Tests
  nuevos en `AnomalyDetailPage.test.tsx` cubriendo CB-01. Confirmar que
  los tests existentes de SPEC-007 en este archivo siguen pasando.
- [ ] **Paso 3: E2E de navegación:** Crear `e2e/navigation.test.tsx`
  según sección 3.3 (los 3 tests descritos, como mínimo).
- [ ] **Paso 4: Validación:** `pnpm build`, `pnpm lint`, `pnpm test` en
  verde (incluyendo TODOS los tests heredados de SPEC-007, no solo los
  nuevos), confirmado independientemente por los arquitectos.
  Verificación visual manual del highlight en al menos 1 caso real
  (recomendado: M-109 o M-112, casos con ventana de anomalía bien
  definida) queda a cargo del usuario antes de la demo.

---

## 6. Verificación y Checklist de Salida (Pipeline de 5 Pasos)

- [ ] **1. Validación Arquitectónica:**
  - `MeterHistoryChart.tsx` sigue sin hacer fetch propio — recibe todo
    por props, incluyendo las 2 props nuevas.
  - `AnomalyDetailPage.tsx` es la única página modificada en este SPEC.
  - Ningún archivo de `api/`, `stores/`, `router.tsx`, layout, ni
    componentes/páginas protegidos de SPEC-005/006/007 fue modificado.
  - `specs/TASK_STATUS.md` no fue tocado.
  - `git diff` coincide únicamente con los archivos autorizados en la
    Sección 1. Cero archivos de `backend/` tocados.
- [ ] **2. Generación de Tests:**
  - Tests nuevos para el highlight de `MeterHistoryChart`, para la
    sección de evidencia visual de `AnomalyDetailPage`, y el primer
    E2E de navegación del proyecto (mínimo 3 escenarios, sección 3.3).
  - Todos los tests heredados de SPEC-007 siguen pasando sin
    modificaciones no autorizadas.
- [ ] **3. Validación de Cobertura:**
  - `pnpm build`, `pnpm lint`, `pnpm test` en verde.
- [ ] **4. Documentación As-Built:**
  - Comentarios JSDoc breves en las props nuevas de `MeterHistoryChart`.
- [ ] **5. Trazabilidad y Estado:**
  - Checklist de este SPEC completado. **La entrada en
    `specs/TASK_STATUS.md` la agregan los arquitectos**, no el agente.
