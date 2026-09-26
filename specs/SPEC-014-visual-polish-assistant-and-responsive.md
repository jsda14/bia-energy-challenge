# SPEC-014 — Pulido Visual: Asistente, Navegación Móvil, Tablas Responsive y Viveza del Dashboard

**Estado:** 🟡 Propuesta, pendiente de aprobación.

## 0. Contexto y motivación

Tras cerrar SPEC-013, la verificación en navegador real (light y dark
mode, viewport mobile) reveló deuda visual acumulada en 4 áreas
concretas: el panel del asistente conversacional (SPEC-013), el botón
de menú hamburguesa en mobile, las tablas convertidas a cards en
mobile, y una falta general de riqueza visual/micro-interacciones en
el Dashboard frente a productos de referencia de la industria.

**No es una SPEC de nueva funcionalidad.** No agrega endpoints, no
toca casos de uso, no cambia ningún contrato de datos — es pulido
visual puro sobre superficies ya existentes y ya auditadas
funcionalmente (SPEC-009 a SPEC-013).

## 1. Hallazgos verificados (no solo percepción — confirmados contra el
código real antes de escribir esta SPEC)

1. **`AssistantPanel` pobre visualmente, sin estado de carga:**
   `AssistantPanel.tsx`/`.module.css` no tienen ningún indicador
   mientras `isPending` es `true` — el usuario no ve nada distinto
   entre enviar un mensaje y recibir la respuesta. Además,
   `AssistantPanel.module.css:164` usa `@media (max-width: 480px)`
   como excepción hacia abajo, violando mobile-first
   (`STANDARDS.md` §4.4) — mismo antipatrón ya corregido dos veces en
   el proyecto (SPEC-006, SPEC-012).
2. **Botón hamburguesa roto visualmente:** `Header.module.css` define
   `.header__menuIcon`/`::before`/`::after` como 3 barras posicionadas
   con `position: relative`/`top: -6px`/`top: 6px`, pero el elemento
   base no tiene un alto explícito ni `position: relative` consistente
   con ese layout — las 3 barras no quedan centradas dentro del botón
   de 44×44px, coincide exactamente con la captura del usuario
   (líneas amontonadas/desalineadas).
3. **Bug real de token inexistente en la tabla responsive:**
   `MetersTable.module.css:150-151`, clase `.neutralVariation`, usa
   `--color-success-text`/`--color-success-bg` — **ninguno de los dos
   existe en `tokens.css`** (confirmado por grep). El navegador cae al
   valor inicial/heredado para ambas propiedades, dejando el texto
   "Dentro de norma" sin color ni fondo reales — mismo tipo de bug ya
   visto dos veces en el proyecto (tokens inventados en
   `MeterStatusDistribution` de SPEC-012). Además, el layout de cards
   mobile (`@media (max-width: 767px)`, línea 73) tiene el mismo
   antipatrón de mobile-first invertido que los hallazgos 1 y 3 de
   SPEC-012.
4. **Dashboard funcionalmente completo pero visualmente plano:** sin
   micro-interacciones, transiciones de entrada, ni skeleton loaders
   consistentes — confirmado por inspección, no hay ningún
   `@keyframes` de entrada aplicado a `StatCard`/gráficos al montar la
   página, y los estados de carga son un simple `<div>Cargando...</div>`
   de texto plano (`DashboardPage.tsx`).

## 2. Alcance

### 2.1 `AssistantPanel` — estado de carga y Markdown

- Agregar un indicador de "escribiendo/pensando" mientras
  `isPending` es `true` — 3 puntos animados o equivalente, con
  `aria-live="polite"` y `aria-busy="true"` en el contenedor de
  mensajes (mismo criterio de accesibilidad ya usado en
  `AiExplanationBlock` para el estado de regeneración, SPEC-011).
  Debe respetar `prefers-reduced-motion` (mismo criterio que el resto
  del sistema de motion "Pulse").
- Reemplazar el render de texto plano de los mensajes del asistente
  (`{msg.text}` en `AssistantPanel.tsx`) por el componente
  **`MarkdownText`** ya existente (`frontend/src/components/ui/MarkdownText.tsx`,
  con `react-markdown`/`remark-gfm` ya instalados desde SPEC-011) — no
  se crea un renderer nuevo, se reutiliza el mismo que ya usa
  `AiExplanationBlock`. Los mensajes de usuario (`role: "user"`)
  siguen como texto plano (no hay razón para interpretar Markdown de
  lo que el propio usuario escribió).
- Corregir el `@media (max-width: 480px)` de `AssistantPanel.module.css`
  a mobile-first real: base sin media query pensada para mobile
  (`width: auto`, `left`/`right: var(--space-2)`), `@media (min-width: 481px)`
  para el ancho fijo de 360px en desktop.
- Revisión visual completa del panel en ambos temas: contraste de
  `.message--assistant`/`.message--user`, visibilidad clara de que el
  panel está abierto: verificar `box-shadow`/`border` con contraste
  suficiente contra el fondo en ambos temas, no solo en el que se
  probó al implementar SPEC-013.

### 2.2 Botón de menú hamburguesa — rediseño

- Corregir el bug de alineación de `.header__menuIcon` (hallazgo #2):
  las 3 barras deben quedar centradas y equidistantes dentro del
  botón, en ambos temas.
- Tratamiento visual "profesional y moderno" (criterio verificable, no
  abierto): transición suave entre el ícono de hamburguesa (☰) y una
  X al abrir el menú (`transform: rotate(...)`/`translateY(...)` en
  las barras vía CSS, sin JS adicional — mismo criterio de
  "animación con `@keyframes`/`transition` declarativa" ya usado en el
  sistema "Pulse"), respetando `prefers-reduced-motion` (fallback:
  cambio instantáneo de ícono sin transición).
- El panel `MobileNav` que se despliega gana una transición de
  entrada (deslizamiento o fade, no aparición abrupta) — igual criterio
  de motion declarativo.

### 2.3 Tablas responsive (cards en mobile) — fix y alineación

- Corregir el bug de token inexistente (hallazgo #3): `.neutralVariation`
  usa `--color-neutral-text`/`--color-neutral` — **no** un color de
  "éxito" inventado (no existe esa categoría semántica en el proyecto;
  "dentro de norma" es el caso neutral de RN-06, mismo criterio de
  `severityToColorToken`/`meterStatusToColorToken`).
- Reescribir `@media (max-width: 767px)` a mobile-first real: layout
  de card como base (sin media query), `@media (min-width: 768px)`
  para la tabla tradicional — mismo fix ya aplicado dos veces en el
  proyecto, este archivo quedó sin corregir en esas rondas anteriores.
- Alineación y espaciado de la card: revisar el `grid-template-areas`
  actual (`"name name" / "status consumption" / "variation severity"`)
  y ajustar gap/padding para que las 2 columnas de cada fila queden
  visualmente balanceadas (mismo ancho aparente), con el label
  (`data-label` vía `::before`) consistente en tamaño/color en las 4
  filas de metadata (todas menos el nombre).
- Aplicar el mismo criterio de revisión a cualquier otra tabla con el
  mismo patrón de card mobile en el proyecto (`AnomaliesTable`, si
  comparte el mismo módulo CSS o un patrón equivalente — verificar
  antes de asumir que es exclusivo de `MetersTable`).

### 2.4 Viveza visual del Dashboard — criterios anclados a Grafana/Vercel

**Referencia de diseño explícita (para evitar el error ya cometido una
vez en SPEC-011 de partir de "genérico/bonito" sin ancla verificable):**
Grafana (densidad de información alta pero limpia, bordes finos,
tipografía monoespaciada para valores numéricos, transiciones sutiles
al cargar paneles) y Vercel Dashboard (cards con sombra discreta y
borde de 1px, micro-interacciones de hover consistentes, skeleton
loaders en vez de texto "Cargando...", transiciones de entrada
escalonadas para elementos de una lista/grid).

Criterios de aceptación concretos (verificables, no "más vivo" abierto):

- **Skeleton loaders:** reemplazar `<div>Cargando...</div>` en las 5
  páginas del proyecto que usan ese mismo patrón de loading de texto
  plano (`DashboardPage`, `MeterListPage`, `MeterDetailPage`,
  `AnomaliesPage`, `AnomalyDetailPage`) — no solo `DashboardPage` — por
  placeholders con la forma real del contenido final de cada una
  (rectángulos con animación de shimmer sutil vía
  `@keyframes`, respetando `prefers-reduced-motion`).
- **Transición de entrada escalonada:** los `StatCard` del Dashboard y
  las cards de `MetersTable`/`AnomaliesTable` en mobile ganan una
  transición de entrada sutil (fade + translateY pequeño) al montar,
  con un `delay` incremental por índice (efecto "stagger", mismo
  patrón que Vercel Dashboard) — implementado en CSS puro (`animation-delay`
  calculado inline o por `:nth-child`), sin librería de animación
  nueva.
- **Micro-interacciones de hover/focus consistentes:** todas las cards
  interactivas (`StatCard`, filas de tabla, cards mobile, tarjetas de
  `TriageList`) comparten una misma transición de elevación/borde al
  hover (`box-shadow`/`border-color`, transición `var(--motion-fast)`),
  auditado para que sea *el mismo* valor en todos los componentes, no
  variantes ligeramente distintas por haberse escrito en momentos
  distintos del proyecto.
- **Tipografía monoespaciada para valores numéricos destacados:**
  los valores de `StatCard` (KPIs) y las cifras de consumo/variación
  en las tablas ganan una fuente monoespaciada (`font-variant-numeric: tabular-nums`
  como mínimo, o una fuente mono si el sistema tipográfico ya definido
  en `tokens.css` lo permite sin agregar una fuente nueva no
  autorizada) — mismo criterio de legibilidad de datos que Grafana.

**Explícitamente fuera de alcance de este criterio:** ninguna
animación con librerías nuevas (`framer-motion`, `gsap`, etc.) — todo
el motion se implementa con CSS puro (`@keyframes`/`transition`),
mismo criterio ya establecido por el sistema "Pulse" desde SPEC-011.
No se rediseña la paleta de colores ni el sistema de tokens — SPEC-011
ya la cerró y quedó aprobada.

## 3. Explícitamente fuera de alcance

- Cualquier cambio de paleta de colores o tokens de diseño (SPEC-011,
  ya cerrada).
- Cualquier librería de animación JS nueva.
- Cambios a lógica de negocio, endpoints, o contratos de datos —
  puramente visual/CSS/estructura de presentación.
- El asistente conversacional y el estado de triage en sí
  (funcionalidad ya cerrada en SPEC-013) — solo se toca su
  presentación visual.

## 4. Verificación exigida antes de aprobar cierre

- Captura de pantalla o verificación en navegador real de los 4
  puntos, en **ambos** temas (light/dark) y en **ambos** viewports
  (mobile <768px, desktop) — no solo el tema/viewport en que se
  implementó.
- `grep` explícito confirmando que no queda ningún token de color
  inventado (`--color-success-*` u otro no presente en `tokens.css`)
  en los archivos tocados.
- Ningún `@media (max-width: ...)` nuevo o remanente como base de
  layout en los archivos tocados (mobile-first estricto, `STANDARDS.md`
  §4.4).
- `pnpm build`/`pnpm lint`/`pnpm test` verificados de forma
  independiente, no solo el reporte de cierre del agente.
- Verificar `prefers-reduced-motion` en cada animación nueva agregada
  (hamburguesa, stagger de entrada, skeleton shimmer, indicador de
  "pensando" del asistente).
