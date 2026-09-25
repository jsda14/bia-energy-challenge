# SPEC: SPEC-011 - Frontend: Rediseño Visual "Bia Pulse" (Identidad de Marca Real + Sistema de Interacción IA)

> **Instrucciones para el Agente Codificador:**
> 1. No instales dependencias externas, librerías ni paquetes que no estén explícitamente autorizados en la sección 2. `react-markdown` + `remark-gfm` ya están instalados (usados por `MarkdownText`) y no se retiran; no se autoriza ninguna dependencia adicional.
> 2. No agregues campos adicionales, métodos auxiliares públicos ni endpoints fuera de los contratos descritos en la sección 3.
> 3. Implementa únicamente las tareas listadas en la sección 5 en orden secuencial. Si encuentras un bloqueo, detén la ejecución y solicita aclaración.
> 4. Sigue el **Protocolo de Fronteras de STANDARDS.md sección 2** sin excepción: antes de tocar cualquier archivo, cotéjalo contra la sección 1 de este SPEC; antes de escribir cualquier firma/prop, cotéjalo contra la sección 3. Si algo no encaja, emite `BLOCKED_BY_BOUNDARY: <archivo/firma> — <razón>` y detente.
> 5. **Este SPEC es visual + un fix puntual de dominio (severidad→color, sección 3.0) + reestructuración del componente de IA (`AiExplanationBlock`, `MarkdownText`) + un componente de navegación mobile nuevo (`MobileNav`).** No cambia ningún otro contrato de `api/`, ni el shape de las respuestas del backend.
> 6. **APROBADO Y EJECUTADO (2026-09-25).** Este documento refleja el resultado final auditado — ver sección 0 para el razonamiento de diseño detrás de cada decisión de paleta/motion.
> 7. **`specs/TASK_STATUS.md` NO se toca.**
> 8. **No modifiques nada de `backend/`.**
> 9. Todo color nuevo debe pasar por `styles/tokens.css` como variable — cero valores hex sueltos en archivos `.module.css` (única excepción ya existente y aceptada: `chartColors.ts`).

---

## 0. Por qué una v3 — diagnóstico de por qué v2 falló

v2 se ejecutó y el resultado fue rechazado por el usuario tras verlo corriendo
en navegador. Diagnóstico punto por punto (verificado leyendo el código
resultante de v2 en el repo, no solo la especificación):

1. **"Se ve genérico, colores típicos de interfaz de IA":** v2 inventó una
   paleta "cobre + verde-osciloscopio" sin ninguna relación con la marca real.
   Ironía del proceso: v2 se escribió *para evitar* verse genérico, pero al
   no anclarse a un asset real terminó siendo *otro* genérico más.
2. **"Se quitó todo lo de Bia Energy, el logo":** correcto y es el error raíz.
   El logo real (`frontend/src/assets/img/bia-icon.jpg`) es un orbe con
   degradé **azul profundo → violeta/púrpura eléctrico**, con un rayo en
   **lila claro** al centro. v2 nunca miró ese archivo con atención —
   asumió una temática "industrial-cobre" que no tiene sustento en ningún
   asset ni comunicación real de la empresa. **Esta v3 corrige esto
   anclando el 100% de la paleta al degradé real del logo.**
3. **"Dashboard básico, rústico, plano":** confirmado en código
   (`DashboardPage.tsx`) — es un `<h1>` + botón + grid de `StatCard`
   idénticas entre sí, sin jerarquía visual, sin franja de marca, sin
   ningún elemento que comunique "producto energético serio". v2 nunca
   tocó la estructura del Dashboard, solo coloreó los mismos bloques planos
   de SPEC-006/009.
4. **"Skeleton feo, texto de fondo raro, falta en Acción Recomendada":**
   confirmado en código (`AiExplanationBlock.module.css` — `.loaderOverlay`
   con `position: absolute` sobre `.textWrapper--generating` en `opacity:
   0.35`) — dos capas visuales compitiendo por el mismo espacio en vez de
   una transición de estado limpia. Y confirmado que `recommended_action`
   en `AnomalyDetailPage.tsx` nunca pasó por el flag `isRegenerating` —
   solo se envolvió con `<MarkdownText>` estático, sin loader, porque la
   respuesta de `POST /anomalies/:id/regenerate-explanation` (ver
   `backend/app/adapters/inbound/api/anomalies_router.py`) actualiza
   *ambos* campos (`reason` y `recommended_action`) en una sola llamada,
   algo que v2 no consideró al diseñar el contrato de `AiExplanationBlock`
   con una sola prop `reason`.
5. **"No hay animaciones bonitas":** v2 sí definió motion tokens y un par de
   keyframes, pero aislados (barrido de header, aguja oscilando) sin
   ningún sistema de entrada/salida para el resto de la UI (cards,
   páginas, filas de tabla) — el resultado percibido es "estático con dos
   detalles animados sueltos", no un sistema.
6. **"Header no responsive":** confirmado — `Header.module.css` solo tiene
   un breakpoint a 480px que pasa de columna a fila; con marca + 3 links +
   badge de estado + toggle de tema, container no cabe cómodo antes de
   `md` (768px) y no existe ningún patrón de menú colapsable para pantallas
   angostas reales (320-479px, el rango donde más se prueba un producto).
7. **"HIGH y MEDIUM mismo color":** confirmado, no es un problema visual —
   es un bug de mapeo en `domain/formatting.ts`,
   `severityToColorToken()`: `MEDIUM` y `HIGH` devuelven ambos
   `"critical"`, y `LOW` devuelve `"warning"` (más grave que `neutral`,
   invertido). Fuera del alcance "solo CSS" de v1/v2 — se corrige acá
   explícitamente porque bloquea el uso correcto de cualquier paleta.

**Principio rector de esta v3:** cada decisión de color se justifica contra
el asset real de marca (`bia-icon.jpg`), no contra una "categoría estética"
inventada (industrial/cobre, tech/lila-genérico, etc.). El nombre en clave
pasa a ser **"Bia Pulse"**: el pulso/latido es la metáfora de movimiento
(ya presente en el rayo del logo) que reemplaza tanto al "glow genérico de
IA" de v1 como al "instrumento industrial" desconectado de marca de v2.

---

## 1. Alcance y Fronteras

### 1.1 Objetivo

Construir la identidad visual de Bia Energy **a partir del asset real**
(`bia-icon.jpg`: orbe con degradé azul-profundo→violeta-eléctrico y rayo
lila), resolver los 7 defectos del punto 0, y entregar un sistema de motion
cohesivo. Modo oscuro como experiencia principal, modo claro con el mismo
acento adaptado a AA. Dashboard con jerarquía visual real. Header con
navegación mobile funcional. Bloque de IA con un único estado de carga
consistente que cubre *ambos* campos que la API actualiza.

### 1.2 Paleta — anclada al logo, verificable a simple vista

Se extrae la paleta directamente de las zonas del logo (no una
interpretación libre):

- **Azul profundo del fondo del orbe** → base de fondo oscuro.
- **Violeta/púrpura eléctrico de la zona media del degradé** → acento
  secundario / superficies elevadas con tinte.
- **Lila claro del rayo** → `--color-primary`, el color de acción e
  identidad (ya era la intuición original del usuario con Gemini en v1 —
  correcta en la elección de tono, el error de v1 fue la ejecución
  "glow gaseoso genérico", no el tono en sí).

**Modo oscuro (default):**

```css
--color-bg: #0A0A1F;            /* azul-noche profundo, tomado del borde
                                    exterior del orbe del logo */
--color-bg-elevated: #14142E;   /* un paso hacia el violeta medio del
                                    degradé, para dar profundidad de capas
                                    sin saltar a navy genérico */
--color-text: #F1F0F9;          /* blanco con tinte lila muy sutil */
--color-text-muted: #9C98C2;
--color-border: rgba(180, 177, 254, 0.14);
--color-primary: #B4B1FE;       /* el lila exacto del rayo del logo */
--color-primary-hover: #CFCCFF;
--color-pulse: #7C6FFF;         /* violeta eléctrico de la zona media del
                                    degradé — reservado para el sistema de
                                    "pulso" (ver 3.2), nunca decorativo
                                    suelto */
```

**Modo claro:** mismo lila de marca, oscurecido lo necesario para AA
(verificar en Paso 1), fondos casi blancos con tinte frío muy leve (no
cálido — el frío es coherente con el azul-violeta de marca, a diferencia
de v2 que metió tinte cálido sin motivo de marca):

```css
--color-bg: #F7F7FC;
--color-bg-elevated: #FFFFFF;
--color-text: #14132B;
--color-text-muted: #625E7D;
--color-border: rgba(20, 19, 43, 0.09);
--color-primary: #6660D9;       /* lila de marca oscurecido — AA real
                                    verificado 4.64:1 sobre --color-bg
                                    (cálculo de luminancia relativa WCAG,
                                    confirmado antes de escribir este
                                    valor, no estimado) */
--color-primary-hover: #564FC4;
--color-pulse: #5B4FE0;         /* AA real verificado 5.40:1 sobre --color-bg */
```

Esto es **verificable a simple vista contra el logo**, a diferencia de la
paleta de v2 que no tenía ninguna relación demostrable con ningún asset
del proyecto — es el criterio que usará el arquitecto para validar esta
sección sin ambigüedad.

### 1.3 Sistema de motion — "Pulse", no "glow" ni "escaneo industrial"

Un único lenguaje de movimiento, reutilizado consistentemente (a
diferencia de v2, que tenía 2-3 efectos aislados sin relación entre sí):
una expansión de anillo concéntrico que se desvanece (`pulse-ring`),
inspirada directamente en el rayo/orbe del logo emitiendo un pulso de
energía. Se usa para: focos de interacción con IA (botones, loader),
indicadores de "en vivo" (análisis corriendo), y como transición de
entrada para elementos que aparecen tras una acción. Ver especificación
exacta en 3.2-3.3. Todo motion respeta `prefers-reduced-motion`.

### 1.4 En Alcance (In-Scope)

- Rediseño completo de `styles/tokens.css`: paleta Bia Pulse (sección
  1.2) para ambos modos, tokens de motion consolidados, tokens RGB
  auxiliares. Reemplaza íntegramente los valores que dejó v2 (Copper
  Signal se descarta por completo, no se mezcla).
- `chartColors.ts`: actualizar a la nueva paleta.
- **Fix de dominio puntual:** `domain/formatting.ts`,
  `severityToColorToken()` — corregir el mapeo (sección 3.0). Es la única
  pieza de este SPEC que toca `domain/` y no es CSS — se documenta con su
  propio contrato exacto y su propia razón (bug preexistente que ninguna
  paleta puede resolver por sí sola).
- Header: rediseño con marca real (franja/acento de degradé sutil del
  logo, no glassmorphism gratuito) + **menú mobile colapsable funcional**
  (sección 3.4) — resuelve el punto 6.
- `RunAnalysisButton`: motion "Pulse" en vez del trazo cónico de v2.
- `StatCard`: jerarquía visual real en el Dashboard (sección 3.5) — no
  solo bordes translúcidos, sino una card destacada + composición con
  más peso visual, resuelve el punto 3.
- `MetersTable`/`AnomaliesTable`: layout responsivo cards en mobile
  (idéntico contrato funcional a v1/v2, sección 3.6 — esta parte de v2 no
  tuvo quejas y se mantiene).
- `Badge`/`DetailField`: pills translúcidos con la nueva paleta.
- **Reestructurar `AiExplanationBlock`** (ya existe, creado por v2) para:
  (a) eliminar el overlay superpuesto y usar un único estado de
  transición limpio (sección 3.7), (b) cubrir tanto `reason` como
  `recommended_action` bajo el mismo loader, ya que la API los actualiza
  juntos (contrato nuevo de props, sección 3.7).
- `MarkdownText` (ya existe, creado por v2) se mantiene tal cual — su
  implementación vía `react-markdown`/`remark-gfm` no tuvo quejas
  específicas del usuario; solo se re-skinnea con la nueva paleta vía su
  `.module.css`.
- Sistema de motion tokens consolidado en `tokens.css` (sección 1.3/3.2).

### 1.5 Fuera de Alcance (Out-of-Scope / Non-Goals)

- Cualquier cambio de comportamiento, estado, lógica de filtrado/orden, o
  contrato de props de componentes NO listados en 1.6.
- Reemplazar `bia-icon.jpg` — se usa tal cual, y esta vez **se muestra en
  el Header** (ver 3.4) en lugar de solo texto, ya que es el ancla misma
  de la identidad de marca de este SPEC.
- Animaciones dependientes de scroll.
- Cualquier cambio en `backend/` — el fix de 3.0 y la reestructuración de
  3.7 son 100% frontend sobre datos que la API ya entrega.
- Librerías de animación adicionales (Framer Motion, GSAP).
- Agregar una 4ª categoría de tono (`Badge`/`StatCard` siguen con
  `neutral`/`warning`/`critical`) — el fix de severidad es de *mapeo*,
  no de agregar un tono nuevo.

### 1.6 Archivos Afectados

**Modificar:**
- `frontend/src/styles/tokens.css`
- `frontend/src/domain/formatting.ts` (**solo** el cuerpo de
  `severityToColorToken`, ver 3.0 — firma y tipo de retorno sin cambios)
- `frontend/src/domain/formatting.test.ts` (si existe; si no existe, se
  crea — ver 3.0, requiere test explícito del fix)
- `frontend/src/components/feature/chartColors.ts`
- `frontend/src/components/layout/Header.tsx` (agregar logo + botón de
  menú mobile — ver 3.4, contrato exacto de qué se agrega)
- `frontend/src/components/layout/Header.module.css`
- `frontend/src/components/layout/AppLayout.module.css`
- `frontend/src/components/ui/RunAnalysisButton.module.css`
- `frontend/src/components/ui/StatCard.module.css`
- `frontend/src/components/ui/StatCard.tsx` (**solo** si la jerarquía de
  3.5 requiere una prop `size`/`emphasis` — ver contrato exacto en 3.5;
  si se resuelve 100% desde `DashboardPage.module.css` con `:nth-child`,
  no tocar)
- `frontend/src/components/ui/Badge.module.css`
- `frontend/src/components/ui/DetailField.module.css`
- `frontend/src/components/ui/MarkdownText.module.css`
- `frontend/src/components/feature/MetersTable.tsx` (si requiere
  `data-label`)
- `frontend/src/components/feature/MetersTable.module.css`
- `frontend/src/components/feature/AnomaliesTable.tsx` (mismo criterio)
- `frontend/src/components/feature/AnomaliesTable.module.css`
- `frontend/src/components/feature/AiExplanationBlock.tsx` (contrato de
  props cambia, ver 3.7)
- `frontend/src/components/feature/AiExplanationBlock.module.css`
- `frontend/src/components/feature/AiExplanationBlock.test.tsx`
- `frontend/src/pages/DashboardPage.tsx` (**solo** para pasar la prop de
  énfasis a la primera `StatCard` si 3.5 lo requiere vía prop — sin tocar
  hooks ni lógica de cálculo de `totalConsumptionDisplay`)
- `frontend/src/pages/DashboardPage.module.css`
- `frontend/src/pages/MeterListPage.module.css`
- `frontend/src/pages/MeterDetailPage.module.css`
- `frontend/src/pages/AnomaliesPage.module.css`
- `frontend/src/pages/AnomalyDetailPage.module.css`
- `frontend/src/pages/AnomalyDetailPage.tsx` (**solo** para pasar
  `recommendedAction` a `AiExplanationBlock` en vez de renderizarlo
  aparte — ver 3.7)
- `frontend/src/pages/AnomalyDetailPage.test.tsx` (ajustar solo si alguna
  aserción dependía del markup movido)

**Crear:**
- `frontend/src/components/ui/MobileNav.tsx` (menú mobile, ver 3.4)
- `frontend/src/components/ui/MobileNav.module.css`
- `frontend/src/components/ui/MobileNav.test.tsx`

**Prohibido modificar:**
- Todo `backend/**`
- `ARCHITECTURE.md`, `STANDARDS.md`, `specs/TASK_STATUS.md`
- `frontend/src/api/**`, `frontend/src/stores/**`, `frontend/src/router.tsx`
- `frontend/src/components/ui/MarkdownText.tsx` (solo su `.css`, ver 1.4)
- `frontend/src/api/queries/useRegenerateExplanation.ts`
- Cualquier `.tsx` no listado arriba
- `frontend/src/assets/img/bia-icon.jpg`

---

## 2. Entorno y Dependencias Permitidas

Cero dependencias nuevas respecto a lo ya instalado por v2
(`react-markdown`, `remark-gfm` permanecen; no se agrega nada).

---

## 3. Contratos e Interfaces (Single Source of Truth)

### 3.0 Fix de dominio — `severityToColorToken` (`domain/formatting.ts`)

**Firma sin cambios:**

```typescript
export function severityToColorToken(severity: string): "neutral" | "warning" | "critical"
```

**Mapeo corregido (contrato exacto, reemplaza el cuerpo actual):**

```typescript
export function severityToColorToken(severity: string): "neutral" | "warning" | "critical" {
  switch (severity) {
    case "LOW":
      return "neutral";
    case "MEDIUM":
      return "warning";
    case "HIGH":
      return "critical";
    default:
      return "neutral";
  }
}
```

Justificación: `LOW` no es una alerta (era incorrectamente `"warning"`),
`MEDIUM` y `HIGH` deben distinguirse visualmente (antes ambos eran
`"critical"`, indistinguibles). Este es el ÚNICO cambio de lógica de todo
el SPEC — requiere test explícito nuevo (o agregado a
`formatting.test.ts` si ya existe) con un caso por cada valor de entrada
(`LOW`, `MEDIUM`, `HIGH`, un string no reconocido) antes de tocar ningún
CSS que dependa de esta función (Paso 1 del plan de ejecución).

### 3.1 Paleta de marca — `styles/tokens.css`

Implementar según sección 1.2, para ambos modos (`:root`,
`:root[data-theme="dark"]`, y el bloque `@media (prefers-color-scheme:
dark)` espejo — mismo patrón ya usado en el archivo). Mantener TODOS los
nombres de variable existentes. Agregar:

- `--color-primary-rgb`, `--color-pulse-rgb`, `--color-bg-rgb` (para
  componer transparencias sin hex sueltos).
- `--color-critical-rgb`, `--color-warning-rgb`, `--color-neutral-rgb`
  (ya existían en la implementación de v2, mantener el patrón).
- Motion tokens consolidados:

```css
--motion-fast: 150ms;
--motion-base: 240ms;
--motion-slow: 420ms;
--ease-pulse: cubic-bezier(0.22, 1, 0.36, 1); /* salida rápida, llegada
  suave — sensación de "emisión de energía", no el overshoot elástico de
  v2 que se sentía más "juguete" que "producto serio" */
--ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
```

Re-derivar `--color-neutral/-text`, `--color-warning/-text`,
`--color-critical/-text` para armonizar con el azul-violeta de fondo
(pueden mantenerse los mismos hues de v2 si ya cumplían AA — solo
re-verificar contra los nuevos `--color-bg`/`--color-bg-elevated` y
redocumentar el ratio).

> Mandato de siempre: valores de modo claro son estimaciones. Verificar
> AA real (≥4.5:1 texto, ≥3:1 gráficos) antes de fijar, documentado en
> comentario.

### 3.2 Sistema "Pulse" — anillo concéntrico (reemplaza trazo cónico +
aguja de v2)

Un único `@keyframes` reutilizado en 3 contextos (botón, indicador de
carga, header "en vivo"):

```css
@keyframes pulse-ring {
  0% {
    box-shadow: 0 0 0 0 rgba(var(--color-primary-rgb), 0.35);
  }
  70% {
    box-shadow: 0 0 0 12px rgba(var(--color-primary-rgb), 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(var(--color-primary-rgb), 0);
  }
}
```

Uso en `RunAnalysisButton` (reemplaza el `::after` cónico de v2):

```css
.button {
  position: relative;
  transition: transform var(--motion-fast) var(--ease-standard);
}
.button:hover:not(:disabled),
.button:focus-visible:not(:disabled) {
  animation: pulse-ring 1.4s var(--ease-pulse) infinite;
}
.button:active:not(:disabled) {
  transform: scale(0.97);
}
```

Uso análogo en el indicador "Analizando…" del header (variante con
`--color-pulse` en vez de `--color-primary`, para diferenciar "acción
disponible" de "proceso en curso").

`@media (prefers-reduced-motion: reduce)`: `animation: none` en todos los
usos — el estado sigue siendo comunicado por texto/color estático, nunca
solo por movimiento.

### 3.3 Header — marca real + franja de degradé sutil

Reemplaza el `::after` de "barrido de escaneo" de v2 por una franja
inferior fija con degradé de marca (estática, no animada — el movimiento
se reserva al sistema Pulse de 3.2 para no saturar):

```css
.header {
  position: sticky;
  top: 0;
  background: rgba(var(--color-bg-rgb), 0.92);
  backdrop-filter: blur(10px); /* mejora progresiva, fallback: color sólido ya cubre legibilidad */
  border-bottom: 1px solid var(--color-border);
  z-index: 10;
}
.header::after {
  content: "";
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(
    90deg,
    var(--color-bg) 0%,
    var(--color-pulse) 50%,
    var(--color-primary) 100%
  );
  opacity: 0.6;
}
```

El logo (`bia-icon.jpg`) se agrega junto al texto de marca en
`Header.tsx` (`<img src={biaIcon} alt="Bia Energy" className={styles.header__logo} />`,
import estático del asset), tamaño fijo pequeño (~28-32px, vía
`--space-*` o un valor de `width`/`height` explícito ya que es un ícono,
no un token de espaciado), consistente con que sea el ancla visual de la
identidad de marca de este SPEC (punto 2 del diagnóstico).

### 3.4 `MobileNav` — menú colapsable (componente nuevo, resuelve punto 6)

**Contrato exacto:**

```typescript
// components/ui/MobileNav.tsx
interface MobileNavProps {
  items: { label: string; to: string }[];
}
export function MobileNav(props: MobileNavProps): JSX.Element;
```

**Comportamiento:** por debajo de `--bp-md` (768px), `Header.tsx`
reemplaza el `<nav>` inline visible por un botón hamburguesa
(`aria-expanded`, `aria-controls`, `aria-label="Abrir menú"`) que al
activarse muestra `<MobileNav items={[...]} />` como panel desplegable
(`position: absolute`, ancho completo, debajo del header) con los mismos
3 links (`NavLink` de `react-router-dom`, mismo patrón de
`isActive`/`header__link--active` ya usado). Estado de abierto/cerrado es
`useState` local en `Header.tsx` (UI efímera de un componente, no
Zustand). Desde `--bp-md` en adelante, el `<nav>` tradicional inline se
muestra y `MobileNav`/el botón hamburguesa quedan ocultos
(`display: none` vía media query) — mismo patrón mobile-first de
STANDARDS.md §4.4 (base = mobile, `min-width` agrega/sobreescribe).

Cierra al hacer click en un link (navegación) o al presionar `Escape`
(accesibilidad de teclado mínima).

**Archivos:** `MobileNav.tsx`, `MobileNav.module.css`,
`MobileNav.test.tsx` (test cubre: abre al click del botón, cierra al
click en un link, cierra con Escape, aria-expanded refleja el estado).

`Header.tsx` cambia para: importar `bia-icon.jpg`, agregar el botón
hamburguesa + `<MobileNav>` condicional, envolver el `<nav>` existente en
una clase que se oculta bajo `--bp-md`. No cambia nada de
`useAnalysisStore` ni del `ThemeToggle` ya existentes.

### 3.5 `StatCard` — jerarquía visual del Dashboard (resuelve punto 3)

**Decisión de diseño:** la primera card ("Consumo Total") se distingue
visualmente del resto — más grande, con acento de marca — para romper la
grilla plana de 5 cards idénticas que hoy hace ver el Dashboard "básico".

**Opción preferida (sin tocar `.tsx`, 100% CSS con `:nth-child`, más
simple y sin riesgo de romper el contrato de `StatCard`):**

```css
/* DashboardPage.module.css */
.dashboard__stats-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);
}
@media (min-width: 640px) {
  .dashboard__stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .dashboard__stats-grid > :first-child {
    grid-column: span 2;
  }
}
@media (min-width: 1024px) {
  .dashboard__stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }
  .dashboard__stats-grid > :first-child {
    grid-column: span 4;
  }
}
```

Combinado con una variante visual en `StatCard.module.css` para la
primera posición (`.dashboard__stats-grid > :first-child .stat-card`
— selector desde el módulo de la página hacia el módulo del componente
NO es válido entre CSS Modules distintos; en su lugar, `StatCard` en sí
gana un modificador `stat-card--featured` aplicado condicionalmente):
esto SÍ requiere una prop en `StatCard`.

**Por lo tanto, el contrato real (elegir esta vía, es la única
consistente con CSS Modules):**

```typescript
// StatCard.tsx — se agrega una prop opcional
interface StatCardProps {
  label: string;
  value: string;
  tone?: "neutral" | "warning" | "critical";
  featured?: boolean; // default false — nuevo, único campo agregado
}
```

`featured=true` aplica `.stat-card--featured`: fondo con degradé sutil
(`linear-gradient` de dos paradas usando `--color-bg-elevated` y
`rgba(var(--color-primary-rgb), 0.08)`), borde en `--color-primary` en
vez de `--color-border`, tipografía de `--stat-card__value` más grande
(`1.5× ` el tamaño base, vía una escala ya definida o un valor explícito
nuevo documentado). `DashboardPage.tsx` pasa `featured` únicamente a la
card de "Consumo Total" (la primera, más relevante del negocio).

Esto es la única prop nueva de todo el SPEC fuera del fix de 3.0 — se
declara explícitamente acá para que la Fase 0 del Protocolo de Fronteras
la coteje sin ambigüedad.

### 3.6 Tablas responsivas — cards en mobile (idéntico contrato a v1/v2)

Sin cambios respecto a lo ya especificado y ya implementado por v2 (no
tuvo quejas del usuario) — se mantiene la implementación existente,
solo se re-skinnea con la paleta de 3.1 si sus `.module.css` referencian
colores que cambiaron de valor.

### 3.7 `AiExplanationBlock` — reestructuración (resuelve punto 4)

**Contrato de props nuevo (reemplaza el de v2):**

```typescript
interface AiExplanationBlockProps {
  reason: string;
  recommendedAction: string; // NUEVO — antes vivía suelto en AnomalyDetailPage.tsx
  isRegenerating: boolean;
  isRegenerateError: boolean;
  onRegenerate: () => void;
}
```

Razón del cambio: `POST /anomalies/:id/regenerate-explanation` actualiza
`reason` Y `recommended_action` en la misma llamada (ver
`backend/app/adapters/inbound/api/anomalies_router.py` y
`regenerate_explanation.py` — sin tocarlos, solo se lee su contrato ya
existente vía `AnomalyDetailResponse`, que no cambia). El componente que
muestra el estado de carga debe cubrir ambos campos, no solo `reason`.

**Estructura visual (reemplaza el overlay `position: absolute` de v2):**

En vez de superponer un loader encima del texto atenuado (lo que generó
la queja de "texto de fondo raro, skeleton superpuesto"), se usa **un
solo contenedor con transición de reemplazo de contenido**, sin dos capas
compitiendo:

1. **Reposo:** dos secciones, "Razón" (`<MarkdownText content={reason}
   />`) y "Acción Recomendada" (`<MarkdownText content={recommendedAction}
   />`), cada una con su título, dentro del mismo componente.
2. **Generando** (`isRegenerating === true`): el contenido de AMBAS
   secciones se reemplaza — no se atenúa ni se superpone — por un bloque
   de skeleton único por sección (líneas `shimmer`, mismo criterio visual
   que antes pero SIN overlay: es contenido reemplazado, controlado por
   render condicional simple, `{isRegenerating ? <Skeleton /> :
   <MarkdownText content={reason} />}`). Encima de ambos bloques, un
   indicador de estado compartido con el sistema Pulse de 3.2 (círculo
   con `animation: pulse-ring`, usando `--color-pulse`) + texto "La IA
   está analizando…". `aria-busy="true"` y `aria-live="polite"` en el
   contenedor raíz, cubriendo ambas secciones a la vez.
3. **Actualizado:** al pasar `isRegenerating: true → false`, ambas
   secciones entran con `@keyframes` `opacity 0→1` +
   `translateY(4px)→0`, `--motion-slow`/`--ease-standard`. Una sola
   etiqueta "Actualizado ahora" (no una por sección) cerca del botón,
   con el mismo criterio de auto-desvanecido por `animation-delay: 3s`
   ya usado en v2 (se mantiene esa técnica, no tuvo quejas).

Si `isRegenerateError`, se muestra el mismo mensaje de error ya existente
(no se modifica ese comportamiento).

**`AnomalyDetailPage.tsx` cambia para:** pasar `recommendedAction=
{anomaly.recommended_action}` a `AiExplanationBlock` y **eliminar** el
bloque separado de "Acción Recomendada" que hoy vive aparte (líneas ~101-104
del archivo actual) — todo el contenido generado por IA vive ahora en un
único componente con un único ciclo de carga coherente.

### 3.8 `MarkdownText` — sin cambios de contrato, solo re-skinning

`MarkdownText.tsx` (creado por v2) no se toca. Su `.module.css` se
actualiza para consumir los tokens de la nueva paleta (3.1) donde
referencie `--color-*` cuyo valor cambió — sin alterar la estructura de
clases ni el uso de `react-markdown`/`remark-gfm`.

### 3.9 Mobile-first táctil

- Botón hamburguesa de `MobileNav`: mínimo 44×44px.
- Botón de regenerar y links del menú mobile: mínimo 44×44px de área
  táctil (igual que v2 ya definía, se mantiene).
- El indicador Pulse + texto "La IA está analizando…" se apilan en
  columna por debajo de `--bp-sm` (mismo criterio que v2, se mantiene).

---

## 4. Reglas de Negocio y Casos Borde

### 4.1 Reglas de Negocio (RN)

- **RN-00 (Fix de severidad verificado con test):** `severityToColorToken`
  devuelve `neutral` para `LOW`, `warning` para `MEDIUM`, `critical` para
  `HIGH`, `neutral` para cualquier otro valor — cubierto por un test
  explícito por cada caso antes de continuar con el resto del SPEC.
- **RN-01 (Cero cambios de comportamiento fuera de 3.0 y 3.7):** ningún
  test heredado de SPEC-005 a SPEC-010 requiere modificación de sus
  aserciones de lógica, salvo las que dependían directamente del mapeo
  incorrecto de severidad (si existieran, se corrigen para reflejar el
  mapeo correcto, documentando el cambio).
- **RN-02 (Contraste AA verificado, no asumido):** todo color de texto
  nuevo o modificado se verifica con cálculo real, documentado en
  comentario — incluye `--color-pulse` en ambos modos.
- **RN-03 (Un solo lugar de verdad para cada color):** cero hex sueltos
  fuera de `tokens.css`/`chartColors.ts`.
- **RN-04 (Paleta verificable contra el asset real):** cada valor de
  `--color-bg`, `--color-bg-elevated`, `--color-primary`, `--color-pulse`
  en modo oscuro debe poder señalarse visualmente en una zona concreta
  de `bia-icon.jpg` — documentado en el comentario de `tokens.css` (ej.
  "tomado del borde exterior del orbe", "tomado del rayo central") para
  que la verificación del arquitecto sea directa, no subjetiva.
- **RN-05 (`AiExplanationBlock` cubre ambos campos IA):** ninguna vista
  de `AnomalyDetailPage` muestra `recommended_action` fuera del ciclo de
  carga compartido con `reason` (verificación manual en Paso 8).

### 4.2 Casos Borde (CB)

- **CB-01 (`backdrop-filter` no soportado):** header legible sin blur
  (fallback: color sólido con alpha ya aplica).
- **CB-02 (Tabla con 1 sola fila en modo card):** se ve igual de bien con
  1 o con 12 filas.
- **CB-03 (`reason`/`recommendedAction` vacíos):** `AiExplanationBlock` y
  `MarkdownText` no rompen ni dejan huecos raros.
- **CB-04 (Tabla Markdown con filas desparejas):** delegado a
  `remark-gfm`, ya cubierto por v2, sin cambios.
- **CB-05 (Regenerar tras error previo):** el estado "generando" se
  muestra igual en el siguiente intento, sin lógica adicional.
- **CB-06 (`prefers-reduced-motion`):** Pulse, shimmer, franja de header
  y transiciones de entrada se desactivan o reducen a cross-fade simple.
- **CB-07 (`MobileNav` abierto y cambio de viewport a desktop):** si el
  usuario gira el dispositivo o redimensiona a `≥md` con el menú mobile
  abierto, el menú se oculta (controlado por CSS `display: none` bajo la
  media query — no requiere JS adicional de resize listener, el estado
  de React puede seguir en `true` pero no se renderiza visualmente).
- **CB-08 (Doble fuente de "está generando" tras el fix de 3.7):** con
  `reason` y `recommendedAction` compartiendo un solo `isRegenerating`,
  no debe quedar ninguna sección mostrando contenido stale mientras la
  otra ya muestra skeleton — ambas cambian atómicamente con el mismo
  booleano (verificado por test de `AiExplanationBlock.test.tsx`).

---

## 5. Plan de Ejecución Secuencial (Atomic Tasks)

- [x] **Paso 1: Fix de severidad:** Implementar 3.0 en
  `domain/formatting.ts`, con test explícito de las 4 ramas ANTES de
  tocar cualquier CSS que dependa de esta función (RN-00).
- [x] **Paso 2: Paleta base en `tokens.css`:** Implementar según 3.1,
  documentando AA real y la referencia visual al logo por cada color
  (RN-04). Agregar tokens RGB y motion consolidados.
- [x] **Paso 3: `chartColors.ts`:** Actualizar a la nueva paleta.
- [x] **Paso 4: Header con logo real + franja de marca:** Según 3.3.
- [x] **Paso 5: `MobileNav` + integración en `Header.tsx`:** Según 3.4,
  con sus tests (abre/cierra/Escape/aria-expanded).
- [x] **Paso 6: `RunAnalysisButton` con sistema Pulse:** Según 3.2,
  respetando `prefers-reduced-motion` (CB-06).
- [x] **Paso 7: `StatCard` con prop `featured` + `Badge`/`DetailField`
  pills:** Según 3.5 y sección "En Alcance", integrar en
  `DashboardPage.tsx` (solo la prop nueva, sin tocar hooks).
- [x] **Paso 8: Reestructurar `AiExplanationBlock` (contrato nuevo de
  3.7) + actualizar `AnomalyDetailPage.tsx`:** Eliminar el overlay
  superpuesto, cubrir `recommendedAction` bajo el mismo ciclo de carga,
  eliminar el bloque suelto de "Acción Recomendada" de la página. Tests
  actualizados cubren CB-08 y RN-05.
- [x] **Paso 9: Re-skinning de `MarkdownText`, tablas responsivas
  (`MetersTable`/`AnomaliesTable`) con la nueva paleta:** Sin cambios de
  estructura, solo tokens. Verificar en `xs`, `md`, `fhd`.
- [x] **Paso 10: Validación:** `pnpm build`, `pnpm lint`, `pnpm test` en
  verde. Verificación visual manual completa contra backend real, ambos
  modos de tema, al menos 3 viewports, específicamente: (a) severidad
  HIGH vs MEDIUM se distinguen a simple vista, (b) menú mobile abre/
  cierra correctamente en `xs`, (c) "Regenerar explicación" muestra un
  único ciclo de carga limpio cubriendo Razón y Acción Recomendada sin
  overlay raro.

---

## 6. Verificación y Checklist de Salida (Pipeline de 5 Pasos)

- [x] **1. Validación Arquitectónica:**
  - Único cambio de lógica de negocio: `severityToColorToken` (3.0),
    con test explícito.
  - `StatCard` gana únicamente la prop `featured?: boolean` — ninguna
    otra prop nueva en ningún componente.
  - `AiExplanationBlock` gana únicamente la prop `recommendedAction:
    string` respecto al contrato de v2.
  - `MobileNav` es 100% nuevo, presentación pura, sin llamadas a `api/`.
  - Cero valores hex sueltos fuera de `tokens.css`/`chartColors.ts`.
  - `specs/TASK_STATUS.md` no fue tocado.
  - `git diff` coincide únicamente con los archivos de la Sección 1.6.
    Cero archivos de `backend/` tocados. Cero dependencias nuevas.
- [x] **2. Generación de Tests:**
  - `formatting.test.ts` cubre las 4 ramas de `severityToColorToken`.
  - `MobileNav.test.tsx` cubre abrir/cerrar/Escape/aria-expanded.
  - `AiExplanationBlock.test.tsx` cubre reposo/generando/actualizado/
    error para AMBOS campos (CB-08, RN-05).
  - Todos los tests heredados de SPEC-005 a SPEC-010 siguen pasando
    (ajustados solo si dependían del mapeo de severidad incorrecto).
- [x] **3. Validación de Cobertura:**
  - `pnpm build`, `pnpm lint`, `pnpm test` en verde.
- [x] **4. Documentación As-Built:**
  - Comentarios de AA verificado en `tokens.css` (RN-02), incluyendo la
    referencia visual al logo por color (RN-04).
- [x] **5. Trazabilidad y Estado:**
  - Checklist de este SPEC completado. La entrada en
    `specs/TASK_STATUS.md` la agregan los arquitectos, no el agente.
