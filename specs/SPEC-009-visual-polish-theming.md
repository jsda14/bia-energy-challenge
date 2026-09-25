# SPEC: SPEC-009 - Frontend: Sistema de Diseño Real, Dark/Light Mode y Fixes de Verificación en Navegador

> **Instrucciones para el Agente Codificador:**
> 1. No instales dependencias externas, librerías ni paquetes que no estén explícitamente autorizados en la sección 2.
> 2. No agregues campos adicionales, métodos auxiliares públicos ni endpoints fuera de los contratos descritos en la sección 3.
> 3. Implementa únicamente las tareas listadas en la sección 5 en orden secuencial. Si encuentras un bloqueo, detén la ejecución y solicita aclaración.
> 4. Sigue el **Protocolo de Fronteras de STANDARDS.md sección 2** sin excepción: antes de tocar cualquier archivo, cotéjalo contra la sección 1 de este SPEC; antes de escribir cualquier firma/prop, cotéjalo contra la sección 3. Si algo no encaja, emite `BLOCKED_BY_BOUNDARY: <archivo/firma> — <razón>` y detente.
> 5. **Este SPEC nace de una verificación real en navegador** (no solo tests/build) contra el backend real corriendo — ver sección 1 para el detalle de cada hallazgo. Reproducí cada uno mentalmente contra el código antes de tocar nada.
> 6. `styles/tokens.css` tenía el comentario `/* Semántica de color base (placeholders hasta SPEC-006) */` desde SPEC-005 — nunca fue reemplazado en SPEC-006/007/008. Este SPEC lo reemplaza por completo. Todo archivo `.module.css` del proyecto ya usa `var(--color-*)` (verificado: 12 de 12 archivos), así que un cambio correcto en `tokens.css` se propaga automáticamente — no hay que tocar los `.module.css` uno por uno para el color, solo para breakpoints/spacing puntuales donde se indique.
> 7. **`specs/TASK_STATUS.md` NO se toca** — misma instrucción que SPEC-007/008, que funcionó las últimas 3 entregas seguidas.
> 8. **No modifiques nada de `backend/`** — este SPEC es exclusivamente frontend. (Nota: el fix de CORS en `backend/app/main.py` ya fue aplicado directamente por los arquitectos, fuera de este SPEC — no es parte de tu alcance ni necesitás tocarlo.)

---

## 1. Alcance y Fronteras

* **Objetivo:** Corregir los hallazgos de la primera verificación real en
  navegador contra el backend real, y reemplazar el sistema de diseño
  placeholder (paleta única sin identidad, sin dark mode, breakpoints
  casi sin usar) por uno real y coherente en toda la app.

* **Hallazgos de la verificación en navegador (fuente de este SPEC):**
  1. **Bug real:** en `MeterHistoryChart`, el label del eje Y
     (`yAxis.name`, ej. "Consumo (kWh)") se renderiza superpuesto sobre
     los primeros valores del gráfico — ECharts posiciona `yAxis.name`
     por defecto encima del eje sin reservarle espacio propio, y el
     `grid` actual no le deja margen. Visto tanto en `MeterDetailPage`
     como en `AnomalyDetailPage` (mismo componente compartido).
  2. **Deuda de diseño confirmada:** `styles/tokens.css` nunca salió de
     su estado "placeholder" de SPEC-005 — paleta de un solo azul
     genérico (`--color-primary: #0066cc`), sin dark mode, sin
     variación tonal real. De 12 archivos `.module.css` del proyecto,
     solo 2 (`Header.module.css`, `MetersFilterBar.module.css`) usan
     algún breakpoint — el resto de la UI (Dashboard, tablas, fichas de
     detalle) no tiene ningún ajuste responsive más allá del `auto-fit`
     de CSS Grid ya existente.
  3. **No es un bug de nuestro código:** el error de consola
     `TypeError: Cannot read properties of undefined (reading
     'profile') at onUpdate-profile` proviene de un archivo
     `index-DPEukVt5.js` ajeno al bundle del proyecto (verificado:
     ningún archivo fuente del repositorio contiene la palabra
     "profile") — es una extensión del navegador inyectándose en la
     página, no algo que este SPEC deba corregir.

* **En Alcance (In-Scope):**
  - Rediseño completo de `styles/tokens.css`: paleta de marca real (no
    el azul Bootstrap-default actual), variables de color duplicadas
    para modo claro y modo oscuro, toggle de tema.
  - `stores/useThemeStore.ts` (Zustand, nuevo): persiste la preferencia
    de tema del usuario.
  - `components/ui/ThemeToggle.tsx` + `.module.css`: control en el
    `Header` para alternar claro/oscuro.
  - Fix del `yAxis.name` superpuesto en `MeterHistoryChart.tsx`.
  - Breakpoints reales aplicados donde corresponde: grillas de
    `StatCard` (Dashboard), fichas de `DetailField` (Meter/Anomaly
    Detail), y densidad de tabla en `laptop`/`xl`/`fhd`/`qhd` según
    `STANDARDS.md` §4.4 ("layouts de datos densos deben aprovechar el
    espacio extra... no centrar contenido con márgenes vacíos
    crecientes").
  - `<title>` del documento: corregir de "frontend" (default de Vite)
    a "Bia Energy" en `index.html`.

* **Fuera de Alcance (Out-of-Scope / Non-Goals):**
  - El error de consola de la extensión del navegador (hallazgo 3
    arriba) — no es código nuestro, no se investiga más.
  - `Ubicación: Unknown` en `MeterDetailPage` — es un dato real que
    viene así del backend/seed (`location` del medidor), no un bug de
    renderizado del frontend. Fuera de alcance de un SPEC de frontend.
  - Cualquier endpoint o dato nuevo del backend.
  - Agregar componentes de UI genéricos no pedidos (modales, toasts,
    tooltips custom) — el pulido es de lo ya construido, no
    funcionalidad nueva.
  - Animaciones/transiciones elaboradas — se permite lo mínimo
    razonable (transición de color al cambiar de tema), no una
    librería de animación ni gestos.
  - Cualquier cambio en `backend/` (el fix de CORS ya está aplicado,
    fuera de este SPEC).

* **Archivos Afectados:**
  * **Crear:**
    - `frontend/src/stores/useThemeStore.ts`
    - `frontend/src/components/ui/ThemeToggle.tsx`
    - `frontend/src/components/ui/ThemeToggle.module.css`
    - `frontend/src/stores/useThemeStore.test.ts`
    - `frontend/src/components/ui/ThemeToggle.test.tsx`
  * **Modificar:**
    - `frontend/src/styles/tokens.css` (rediseño completo, sección 3.1)
    - `frontend/src/components/layout/Header.tsx` (agregar `ThemeToggle`)
    - `frontend/src/components/layout/Header.module.css` (si hace falta
      ajuste de layout para el nuevo control)
    - `frontend/src/components/feature/MeterHistoryChart.tsx` (fix del
      `yAxis.name`, sección 3.2)
    - `frontend/src/pages/DashboardPage.module.css` (breakpoints reales
      en la grilla de `StatCard`)
    - `frontend/src/pages/MeterDetailPage.module.css` (breakpoints en
      la grilla de `DetailField`)
    - `frontend/src/pages/AnomalyDetailPage.module.css` (ídem)
    - `frontend/src/components/feature/MetersTable.module.css` /
      `AnomaliesTable.module.css` (densidad en `laptop`/`xl`/`fhd`/`qhd`
      si no la tienen ya)
    - `frontend/index.html` (`<title>`)
    - `frontend/src/main.tsx` (si hace falta aplicar el atributo de
      tema al `<html>`/`<body>` al montar — ver sección 3.1)
  * **Prohibido modificar:**
    - Todo `backend/**`
    - `readings.csv`, `events.csv`
    - `ARCHITECTURE.md`, `STANDARDS.md`
    - `specs/TASK_STATUS.md`
    - `frontend/src/api/**`, `frontend/src/stores/useAnalysisStore.ts`,
      `frontend/src/router.tsx`
    - Cualquier archivo `.tsx` que no esté listado arriba — este SPEC
      es mayormente CSS + 1 store nuevo + 1 componente nuevo + 1 fix
      puntual de chart, no una reescritura de componentes.

---

## 2. Entorno y Dependencias Permitidas

* Ninguna dependencia nueva. Dark mode se implementa con CSS custom
  properties + un atributo `data-theme` en el elemento raíz (patrón
  estándar, sin librerías de theming). Persistencia de la preferencia
  vía Zustand (ya instalado) — no se usa `localStorage` directamente
  fuera de un store, para mantener la disciplina de estado ya fijada en
  `STANDARDS.md` §4.1.

---

## 3. Contratos e Interfaces (Single Source of Truth)

### 3.1 `styles/tokens.css` — rediseño completo

Reemplaza `--color-*` existentes por un sistema con modo claro (default,
`:root`) y modo oscuro (`:root[data-theme="dark"]`). Mantiene TODOS los
nombres de variable ya usados en el código (`--color-bg`, `--color-text`,
`--color-text-muted`, `--color-border`, `--color-primary`,
`--color-neutral`, `--color-neutral-text`, `--color-warning`,
`--color-warning-text`, `--color-critical`, `--color-critical-text`) —
**no renombres ninguna**, ya que 12 archivos `.module.css` las
referencian por nombre exacto; cambiás solo sus valores y agregás el
bloque `[data-theme="dark"]`.

```css
:root {
  /* Paleta de marca — energía/datos, NO el azul Bootstrap-default
     anterior. Elegí un primary con identidad propia (ej. un teal/cyan
     o un ámbar-eléctrico, a tu criterio dentro de lo profesional/
     "SaaS de datos", evitando el azul #0066cc genérico exacto que
     tenía el placeholder). Verificá contraste AA (4.5:1 texto normal)
     contra --color-bg en ambos modos. */
  --color-bg: #...;
  --color-bg-elevated: #...; /* NUEVO: para cards/tablas sobre el fondo base, distinto de --color-bg */
  --color-text: #...;
  --color-text-muted: #...;
  --color-border: #...;
  --color-primary: #...;
  --color-primary-hover: #...; /* NUEVO: estado hover de elementos interactivos con --color-primary */

  --color-neutral: #...;
  --color-neutral-text: #...;
  --color-warning: #...;
  --color-warning-text: #...;
  --color-critical: #...;
  --color-critical-text: #...;

  /* resto de tokens (breakpoints, tipografía, espaciado, radios,
     sombra) se mantienen sin cambios de SPEC-005 */
}

:root[data-theme="dark"] {
  --color-bg: #...;
  --color-bg-elevated: #...;
  --color-text: #...;
  --color-text-muted: #...;
  --color-border: #...;
  --color-primary: #...;
  --color-primary-hover: #...;

  --color-neutral: #...;
  --color-neutral-text: #...;
  --color-warning: #...;
  --color-warning-text: #...;
  --color-critical: #...;
  --color-critical-text: #...;
}

/* Sin data-theme explícito: seguir la preferencia del sistema
   operativo como fallback antes de que el usuario elija manualmente. */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    /* mismos valores que :root[data-theme="dark"] arriba */
  }
}
```

> `--color-bg-elevated` y `--color-primary-hover` son las únicas 2
> variables NUEVAS autorizadas — todo lo demás reutiliza nombres
> existentes. Si necesitás un token adicional para el `ThemeToggle` en
> sí (ej. color del ícono), reusá `--color-text`/`--color-primary`, no
> inventes uno nuevo sin necesidad real.

### 3.2 `stores/useThemeStore.ts`

```typescript
import { create } from "zustand";

type Theme = "light" | "dark";

interface ThemeState {
  theme: Theme;
  toggleTheme: () => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  // Lee de localStorage al inicializar (clave "bia-energy-theme"); si
  // no hay preferencia guardada, default "light" (el toggle visual
  // decide; prefers-color-scheme ya cubre el caso "sin elección
  // explícita" a nivel CSS puro, sección 3.1).
  theme: (typeof localStorage !== "undefined" &&
    (localStorage.getItem("bia-energy-theme") as Theme | null)) || "light",
  toggleTheme: () =>
    set((state) => {
      const next: Theme = state.theme === "light" ? "dark" : "light";
      try {
        localStorage.setItem("bia-energy-theme", next);
      } catch {
        // localStorage puede no estar disponible (modo privado, etc.) — no rompe la UI.
      }
      return { theme: next };
    }),
}));
```

> El store NO aplica el atributo `data-theme` al DOM directamente (eso
> violaría "store puro, sin side-effects de IO" del criterio ya fijado
> en `STANDARDS.md` §4.1) — quien lo aplica es un efecto en
> `main.tsx` o `AppLayout.tsx` (a tu criterio cuál, mientras sea uno
> solo) que observa `useThemeStore().theme` y setea
> `document.documentElement.dataset.theme` en un `useEffect`.

### 3.3 `components/ui/ThemeToggle.tsx`

```typescript
export function ThemeToggle(): JSX.Element { ... }
```

Sin props — lee y escribe directamente `useThemeStore` (mismo criterio
de excepción ya documentado para `RunAnalysisButton` en SPEC-006:
componente de acción conectado al store, no de presentación pura).
Botón simple con ícono/texto que indica el modo destino (ej. "🌙" en
modo claro para pasar a oscuro, "☀️" en modo oscuro para pasar a claro,
o el texto equivalente — a tu criterio del lenguaje visual, mientras
sea claro y accesible con `aria-label`).

### 3.4 `components/layout/Header.tsx`

Se agrega `<ThemeToggle />` al layout existente del header (junto al
indicador de "análisis en curso" ya existente de SPEC-005) — sin alterar
la estructura de navegación (Dashboard/Medidores/Anomalías) ya aprobada.

### 3.5 Fix de `MeterHistoryChart.tsx` — `yAxis.name`

El `yAxis` (y el `yAxis[1]` cuando `compareEnabled`) debe reservar
espacio real para su `name` en vez de superponerlo sobre los datos.
Aplicá **una** de estas soluciones de ECharts (a tu criterio, la que dé
mejor resultado visual):
- `nameLocation: "middle"` + `nameGap` suficiente (ej. 40-50) para que
  el nombre quede como un título de eje rotado fuera del área de
  ploteo, no superpuesto.
- O `grid: { top: "15%", ... }` (ajustando el valor actual) para dejarle
  espacio arriba junto con `nameLocation: "end"` (comportamiento
  default, pero con margen reservado).

Verificar visualmente (no solo que el build pase) que el label ya no se
superpone con los primeros puntos de datos — el checklist de salida de
este SPEC exige explícitamente esta verificación manual antes de cerrar.

### 3.6 Breakpoints reales — criterio general

`STANDARDS.md` §4.4 ya define la escala. Aplicá como mínimo:
- **Grilla de `StatCard` (Dashboard):** ya usa `auto-fit`/`minmax` (CSS
  Grid intrínseco) — mantenelo, pero agregá un ajuste explícito en
  `laptop`/`xl` para que en pantallas grandes las 4 tarjetas usen mejor
  el ancho disponible en vez de solo estirarse por `auto-fit` (ej. un
  `max-width` del contenedor o gap mayor, a tu criterio).
- **Fichas de `DetailField` (`MeterDetailPage`/`AnomalyDetailPage`):**
  columna única en `xs`/`sm`, 2 columnas desde `md`, 3 columnas desde
  `lg`/`laptop` — actualmente es una grilla fija sin ese ajuste
  progresivo.
- **Tablas (`MetersTable`/`AnomaliesTable`):** ya tienen
  `overflow-x: auto` (SPEC-006/007) para `xs`/`sm` — agregá, desde
  `laptop` en adelante, `padding`/`font-size` ligeramente mayor en las
  celdas (más "aire", consistente con "no centrar contenido con
  márgenes vacíos crecientes" de `STANDARDS.md` §4.4 — el objetivo es
  que la tabla se sienta usada a pantalla completa, no un bloque angosto
  perdido en medio de una pantalla FHD/QHD).

---

## 4. Reglas de Negocio y Casos Borde

### 4.1 Reglas de Negocio (RN)

- **RN-01 (Contraste mínimo):** todo par texto/fondo del nuevo sistema
  de color debe cumplir contraste AA (4.5:1 para texto normal, 3:1 para
  texto grande/ícono) en ambos modos — no se acepta un modo oscuro con
  texto gris sobre gris ilegible.
- **RN-02 (Sin flash de tema incorrecto):** el atributo `data-theme` se
  aplica lo antes posible al montar (en el primer `useEffect` del
  componente raíz, no en una página específica) para minimizar el
  "flash" de tema incorrecto al cargar.
- **RN-03 (Tokens únicos, sin duplicación de paleta fuera de
  `tokens.css`):** ningún `.module.css` define un color hardcodeado
  nuevo — todo pasa por las variables de la sección 3.1. Única
  excepción ya existente y aceptada: `chartColors.ts` (SPEC-007), que
  este SPEC puede (opcionalmente) actualizar para que sus 3 constantes
  hex reflejen la nueva paleta, si cambia el primary/critical — a tu
  criterio si el contraste visual lo amerita, documentando el cambio si
  lo hacés.

### 4.2 Casos Borde (CB)

- **CB-01 (`localStorage` no disponible):** `useThemeStore` no debe
  lanzar si `localStorage` está bloqueado (modo privado estricto) — cae
  a `"light"` por defecto sin romper el render.
- **CB-02 (Usuario sin preferencia de sistema):** sin `data-theme`
  explícito y sin soporte de `prefers-color-scheme` en el navegador, el
  `:root` base (modo claro) aplica igual — comportamiento seguro por
  default.

---

## 5. Plan de Ejecución Secuencial (Atomic Tasks)

- [x] **Paso 1: Rediseño de `tokens.css`:** Implementar la paleta real
  (claro + oscuro) según sección 3.1, verificando contraste AA con una
  herramienta de tu elección antes de continuar (documentá los valores
  hex elegidos y su ratio de contraste en un comentario en el propio
  archivo).
- [x] **Paso 2: `useThemeStore` + aplicación de `data-theme`:**
  Implementar el store (sección 3.2) + el efecto que aplica el atributo
  al DOM (RN-02). Test del store.
- [x] **Paso 3: `ThemeToggle` + integración en `Header`:** Implementar
  el componente (sección 3.3) y agregarlo al header (sección 3.4). Test
  del componente (click alterna el tema, refleja el estado del store).
- [x] **Paso 4: Fix de `MeterHistoryChart`:** Corregir el `yAxis.name`
  superpuesto (sección 3.5). Verificar visualmente en el navegador
  (arrancando `pnpm dev` contra el backend real ya corriendo) que el
  label ya no se superpone, en `MeterDetailPage` y `AnomalyDetailPage`.
- [x] **Paso 5: Breakpoints reales:** Aplicar los ajustes de la sección
  3.6 a Dashboard, Meter/Anomaly Detail, y las 2 tablas.
- [x] **Paso 6: `<title>`:** Corregir `index.html`.
- [x] **Paso 7: Validación:** `pnpm build`, `pnpm lint`, `pnpm test` en
  verde (incluyendo TODOS los tests heredados). Verificación visual
  manual en al menos 3 viewports (`xs`, `laptop`, `fhd`) y en ambos
  modos de tema, contra el backend real corriendo — no alcanza con que
  compile, tiene que verse bien.

---

## 6. Verificación y Checklist de Salida (Pipeline de 5 Pasos)

- [x] **1. Validación Arquitectónica:**
  - `ThemeToggle.tsx` es la única excepción nueva autorizada a tocar
    `stores/` directamente (mismo criterio que `RunAnalysisButton`).
  - `useThemeStore.ts` no aplica `data-theme` al DOM él mismo (RN de
    3.2) — eso vive en un efecto separado.
  - Ningún `.module.css` tiene un color hardcodeado fuera de
    `var(--color-*)` (RN-03), salvo `chartColors.ts` si se actualizó
    intencionalmente.
  - `specs/TASK_STATUS.md` no fue tocado.
  - `git diff` coincide únicamente con los archivos autorizados en la
    Sección 1. Cero archivos de `backend/` tocados.
- [x] **2. Generación de Tests:**
  - Tests para `useThemeStore` (toggle alterna el valor, CB-01) y
    `ThemeToggle` (click dispara el toggle, refleja el label/ícono
    correcto según el estado).
  - Todos los tests heredados de SPEC-005 a 008 siguen pasando.
- [x] **3. Validación de Cobertura:**
  - `pnpm build`, `pnpm lint`, `pnpm test` en verde.
- [x] **4. Documentación As-Built:**
  - Comentario en `tokens.css` documentando los ratios de contraste
    verificados para el primary/critical en ambos modos.
- [x] **5. Trazabilidad y Estado:**
  - Checklist de este SPEC completado. **La entrada en
    `specs/TASK_STATUS.md` la agregan los arquitectos**, no el agente.
