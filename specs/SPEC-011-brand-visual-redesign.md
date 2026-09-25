# SPEC: SPEC-011 - Frontend: Rediseño Visual con Identidad de Marca Bia Energy

> **Instrucciones para el Agente Codificador:**
> 1. No instales dependencias externas, librerías ni paquetes que no estén explícitamente autorizados en la sección 2.
> 2. No agregues campos adicionales, métodos auxiliares públicos ni endpoints fuera de los contratos descritos en la sección 3.
> 3. Implementa únicamente las tareas listadas en la sección 5 en orden secuencial. Si encuentras un bloqueo, detén la ejecución y solicita aclaración.
> 4. Sigue el **Protocolo de Fronteras de STANDARDS.md sección 2** sin excepción: antes de tocar cualquier archivo, cotéjalo contra la sección 1 de este SPEC; antes de escribir cualquier firma/prop, cotéjalo contra la sección 3. Si algo no encaja, emite `BLOCKED_BY_BOUNDARY: <archivo/firma> — <razón>` y detente.
> 5. **Este SPEC es 100% visual (CSS Modules + `tokens.css`).** No cambies comportamiento, estado (Zustand/TanStack Query), lógica de filtrado/orden, ni ningún contrato de props existente — solo estilos. Si un cambio visual pareciera requerir tocar lógica de un componente, detenete y preguntá antes de hacerlo.
> 6. **Este SPEC se ejecuta DESPUÉS de SPEC-010** (fixes de UX/funcionalidad) — construye sobre los componentes nuevos que esa SPEC agrega (`AnomaliesFilterBar`, `Breadcrumb`, `SourceBadge` si no fue bloqueado, checkboxes multi-variable de `MeterHistoryChart`). Confirmá que SPEC-010 está cerrada antes de empezar; si algún archivo que este SPEC espera modificar no existe todavía con la forma esperada, emití `BLOCKED_BY_BOUNDARY` y preguntá.
> 7. **`specs/TASK_STATUS.md` NO se toca.**
> 8. **No modifiques nada de `backend/`.**
> 9. Todo color nuevo debe pasar por `styles/tokens.css` como variable — cero valores hex sueltos en archivos `.module.css` (única excepción ya existente y aceptada: `chartColors.ts`, que este SPEC sí actualiza para reflejar la nueva paleta, sección 3.6).

---

## 1. Alcance y Fronteras

* **Objetivo:** Reemplazar la paleta Teal/Slate de SPEC-009 por la
  identidad de marca real de Bia Energy (extraída de
  `frontend/src/assets/img/bia-icon.jpg`, un asset real del proyecto),
  con modo oscuro como experiencia principal, efectos de glow sutiles en
  la interacción de IA, y un layout de tablas responsivo que se
  transforma en tarjetas apiladas en mobile.

* **Decisiones de diseño ya aprobadas por el usuario (no reabrir
  discusión):**
  - Paleta: Deep Midnight Navy (`#050827` fondo base, `#0E123F`
    superficies elevadas) + Electric Lilac (`#B4B1FE` primary,
    `#C9C7FF` hover) — contraste verificado ≥9:1 en ambos casos contra
    los fondos navy (AA ampliamente superado).
  - Efectos de glow sutiles autorizados en el botón de análisis
    (`RunAnalysisButton`) y estados hover relacionados con IA.
  - Modo oscuro es el modo principal/default; modo claro usa blancos y
    grises muy claros con el mismo lila de acento.
  - Tablas se transforman en cards apiladas en `xs`/`sm`, vuelven a
    tabla tradicional desde `md`.

* **En Alcance (In-Scope):**
  - Rediseño completo de `styles/tokens.css`: nueva paleta (reemplaza
    la de SPEC-009) para modo claro y oscuro, manteniendo TODOS los
    nombres de variable existentes (no romper los 12+ archivos que ya
    los consumen).
  - `chartColors.ts`: actualizar las 3 constantes hex para reflejar la
    nueva paleta.
  - Header con estilización de marca (logo o texto estilizado en Electric
    Lilac), sticky con glassmorphism sutil (`backdrop-filter`).
  - `RunAnalysisButton`: efecto glow en hover/focus, transición de
    escala en `:active`.
  - `StatCard`: bordes translúcidos tintados con el primary
    (`rgba(180, 177, 254, 0.15)` o el valor exacto que corresponda a la
    paleta final).
  - `MetersTable`/`AnomaliesTable`: layout responsivo completo —
    tabla tradicional desde `md`, cards apiladas en `xs`/`sm` (ver
    contrato exacto en sección 3.4).
  - `Badge`/`DetailField`: estilo "pill" con fondos translúcidos en vez
    de sólidos opacos.
  - Ajustes de padding/espaciado táctil mobile-first donde corresponda
    (sin cambiar la escala de `--space-*` ya definida, solo su
    aplicación).

* **Fuera de Alcance (Out-of-Scope / Non-Goals):**
  - Cualquier cambio de comportamiento, estado, lógica de filtrado/orden,
    o contrato de props — ver instrucción 5.
  - Reemplazar el asset `bia-icon.jpg` por uno nuevo o generar variantes
    (favicon, etc.) — fuera de alcance, se usa el logo tal cual existe.
  - Animaciones complejas (parallax, scroll-triggered, etc.) — solo
    transiciones simples de hover/focus/active ya autorizadas.
  - Cualquier cambio en `backend/`.
  - Tocar `specs/TASK_STATUS.md`.

* **Archivos Afectados:**
  * **Modificar (todos ya existentes, solo estilos):**
    - `frontend/src/styles/tokens.css`
    - `frontend/src/components/feature/chartColors.ts`
    - `frontend/src/components/layout/Header.module.css`
    - `frontend/src/components/layout/AppLayout.module.css`
    - `frontend/src/components/ui/RunAnalysisButton.module.css`
    - `frontend/src/components/ui/StatCard.module.css`
    - `frontend/src/components/ui/Badge.module.css`
    - `frontend/src/components/ui/DetailField.module.css`
    - `frontend/src/components/feature/MetersTable.tsx` (solo si el
      layout responsivo de cards requiere `data-label` u otro atributo
      HTML para el CSS — ver sección 3.4; si se resuelve 100% con CSS
      puro sin tocar el `.tsx`, no lo toques)
    - `frontend/src/components/feature/MetersTable.module.css`
    - `frontend/src/components/feature/AnomaliesTable.tsx` (mismo
      criterio que `MetersTable.tsx`)
    - `frontend/src/components/feature/AnomaliesTable.module.css`
    - `frontend/src/pages/DashboardPage.module.css`
    - `frontend/src/pages/MeterListPage.module.css`
    - `frontend/src/pages/MeterDetailPage.module.css`
    - `frontend/src/pages/AnomaliesPage.module.css`
    - `frontend/src/pages/AnomalyDetailPage.module.css`
  * **Prohibido modificar:**
    - Todo `backend/**`
    - `ARCHITECTURE.md`, `STANDARDS.md`, `specs/TASK_STATUS.md`
    - `frontend/src/api/**`, `frontend/src/stores/**`, `frontend/src/router.tsx`
    - Cualquier archivo `.tsx` no listado arriba (este SPEC es CSS —
      los `.tsx` listados solo se tocan si es estrictamente necesario
      para un atributo HTML que el CSS responsivo requiera, nunca para
      lógica)
    - `frontend/src/assets/img/bia-icon.jpg` (usar tal cual existe)

---

## 2. Entorno y Dependencias Permitidas

* Ninguna dependencia nueva. `backdrop-filter` es CSS nativo (con
  fallback simple si el navegador no lo soporta — no bloqueante).

---

## 3. Contratos e Interfaces (Single Source of Truth)

### 3.1 Paleta de marca — `styles/tokens.css`

Mantiene TODOS los nombres de variable ya usados (`--color-bg`,
`--color-bg-elevated`, `--color-text`, `--color-text-muted`,
`--color-border`, `--color-primary`, `--color-primary-hover`,
`--color-neutral`, `--color-neutral-text`, `--color-warning`,
`--color-warning-text`, `--color-critical`, `--color-critical-text`) —
cambia solo sus valores.

```css
:root[data-theme="dark"] {
  --color-bg: #050827;           /* Deep Midnight Navy */
  --color-bg-elevated: #0E123F;  /* superficie elevada */
  --color-text: #F5F4FF;         /* blanco cálido, no #fff puro */
  --color-text-muted: #9C99C7;   /* lila apagado, legible sobre navy */
  --color-border: rgba(180, 177, 254, 0.15); /* lila translúcido */
  --color-primary: #B4B1FE;      /* Electric Lilac */
  --color-primary-hover: #C9C7FF;
  /* --color-neutral/-text, --color-warning/-text, --color-critical/-text:
     mantené los de SPEC-009 (ya verificados AA) o ajustá el tono para
     que armonicen con el navy — en cualquier caso, RE-VERIFICÁ contraste
     AA contra --color-bg-elevated (el fondo típico de badges/cards) y
     documentalo en el comentario del archivo, mismo criterio que
     SPEC-009. */
}

:root {
  /* Modo claro: blancos y grises muy claros, mismo primary lila */
  --color-bg: #FAFAFC;
  --color-bg-elevated: #FFFFFF;
  --color-text: #16142B;         /* casi negro con tinte navy */
  --color-text-muted: #635F87;
  --color-border: rgba(15, 8, 39, 0.1);
  --color-primary: #6E69D6;      /* lila MÁS OSCURO que en dark mode —
                                     #B4B1FE sobre fondo claro NO cumple
                                     AA (verificalo vos mismo antes de
                                     usarlo), necesita un tono más
                                     saturado/oscuro para legibilidad en
                                     modo claro */
  --color-primary-hover: #5A54C4;
  /* mismo criterio que arriba para neutral/warning/critical */
}
```

> El valor exacto de `--color-primary` en modo claro es una
> **estimación** — la instrucción obligatoria es: **verificá contraste
> AA real (≥4.5:1) contra `--color-bg` antes de fijar el valor final**,
> ajustando el tono de lila hasta cumplir, documentando el ratio
> verificado en un comentario (mismo formato que SPEC-009).

### 3.2 `RunAnalysisButton` — efecto glow

```css
/* RunAnalysisButton.module.css, agregar: */
.button {
  /* ... estilos existentes ... */
  transition: box-shadow 0.2s ease, transform 0.15s ease;
}
.button:hover:not(:disabled) {
  box-shadow: 0 0 16px 2px rgba(180, 177, 254, 0.4); /* glow sutil, tintado con --color-primary */
}
.button:active:not(:disabled) {
  transform: scale(0.97);
}
```

Usá `var(--color-primary)` para derivar el color del glow (vía una
variable RGB auxiliar si hace falta, ej. `--color-primary-rgb: 180, 177,
254;` en `tokens.css`, para poder componer `rgba(var(--color-primary-rgb),
0.4)` sin hardcodear el hex del glow por separado del token real).

### 3.3 Header — glassmorphism sutil

```css
/* Header.module.css, agregar al selector del header: */
.header {
  position: sticky;
  top: 0;
  backdrop-filter: blur(12px);
  background: rgba(5, 8, 39, 0.85); /* --color-bg con alpha, vía la
                                        misma técnica de variable RGB
                                        auxiliar que el glow */
  border-bottom: 1px solid var(--color-border);
}
```

Ajustar el valor de `background` para modo claro de forma análoga
(usando `--color-bg` claro con alpha).

### 3.4 Tablas responsivas — cards en mobile

**Contrato de comportamiento exacto:**
- Desde `--bp-md` (768px) en adelante: tabla tradicional, sin cambios
  respecto al layout actual (ya funciona bien en desktop).
- Por debajo de `--bp-md` (`xs`/`sm`): cada `<tr>` se convierte
  visualmente en una card (bloque con borde, padding, sombra sutil),
  cada `<td>` pasa a `display: flex; justify-content: space-between`
  mostrando su valor junto a un label del nombre de columna.
- **Cómo obtener el label de columna sin JS**, a elección tuya entre dos
  técnicas CSS estándar (documentá cuál usaste):
  a) Atributo `data-label` en cada `<td>` (requiere tocar el `.tsx` de
     `MetersTable`/`AnomaliesTable` para agregarlo) + CSS
     `content: attr(data-label)` en un pseudo-elemento `::before`.
  b) CSS puro con `nth-child` + `content: "Nombre columna"` fijo en el
     `::before` de cada posición de columna (sin tocar el `.tsx`, pero
     más frágil si el orden de columnas cambia en el futuro).
- La fila deja de tener el comportamiento de `role="button"` visual de
  tabla (hover de fila completa) pero SIGUE siendo clickeable/accesible
  por teclado igual que antes — no se toca la lógica de
  `onClick`/`onKeyDown`/`tabIndex`/`role` ya existente en el `.tsx`
  (instrucción 5: sin cambios de comportamiento), solo el CSS que la
  envuelve visualmente.
- Los headers ordenables (`<button>` dentro de `<th>`) dejan de ser
  visibles en el modo card de mobile (no hay `<thead>` visible) — el
  orden sigue siendo posible solo desde `md` en adelante en este SPEC
  (agregar orden accesible en modo card queda fuera de alcance, no
  pedido).

### 3.5 `Badge`/`DetailField` — estilo pill translúcido

```css
/* Badge.module.css, ejemplo para tone="critical": */
.badge--critical {
  background: rgba(var(--color-critical-rgb), 0.15); /* translúcido, no sólido opaco */
  color: var(--color-critical-text);
  border: 1px solid rgba(var(--color-critical-rgb), 0.3);
  border-radius: 999px; /* pill */
}
```

Mismo criterio para `tone="warning"`/`"neutral"`. Necesitarás agregar
variables RGB auxiliares en `tokens.css` para `--color-critical`,
`--color-warning`, `--color-neutral` (mismo patrón que
`--color-primary-rgb` de la sección 3.2), ya que CSS no puede extraer
componentes RGB de un valor hex existente sin declararlos por separado.

### 3.6 `chartColors.ts` — actualización

```typescript
// Debe mantenerse sincronizado a mano con styles/tokens.css
export const CHART_COLOR_SERIES_A = "#B4B1FE";   // --color-primary (dark mode)
export const CHART_COLOR_SERIES_B = "#9C99C7";   // --color-text-muted (dark mode)
export const CHART_COLOR_BASELINE = "#F5A3A3";   // rojo suave legible sobre navy — ajustar si no cumple contraste
// Si SPEC-010 agregó una 3ra/4ta constante para el multi-variable, actualizarlas también aquí con el mismo criterio.
```

> Nota: `chartColors.ts` no tiene acceso a `[data-theme]` (son
> constantes JS, no CSS) — igual que en SPEC-007/009, se fija un único
> set de colores optimizado para el modo oscuro (el modo principal del
> proyecto según la decisión de esta SPEC), aceptando que en modo claro
> el chart puede verse ligeramente menos ajustado a la paleta — no
> bloqueante, ya era así desde SPEC-007.

---

## 4. Reglas de Negocio y Casos Borde

### 4.1 Reglas de Negocio (RN)

- **RN-01 (Cero cambios de comportamiento):** ningún test heredado de
  SPEC-005 a SPEC-010 debe requerir modificación de sus aserciones de
  lógica — solo pueden verse afectados tests que hagan snapshot/
  assertion directa de una clase CSS específica (poco común en este
  proyecto, que usa roles/texto para las aserciones).
- **RN-02 (Contraste AA verificado, no asumido):** todo color de texto
  nuevo o modificado se verifica con cálculo real de contraste antes de
  fijarse, documentado en comentario — mismo criterio que SPEC-009.
- **RN-03 (Un solo lugar de verdad para cada color):** cero valores hex
  sueltos fuera de `tokens.css`/`chartColors.ts` (instrucción 9).

### 4.2 Casos Borde (CB)

- **CB-01 (`backdrop-filter` no soportado):** el header sigue siendo
  legible sin el efecto de blur (fallback: el `background` con alpha ya
  aplica igual, `backdrop-filter` es una mejora progresiva).
- **CB-02 (Tabla con 1 sola fila en modo card):** el layout de card debe
  verse igual de bien con 1 o con 12 filas — no depende de la cantidad.

---

## 5. Plan de Ejecución Secuencial (Atomic Tasks)

- [ ] **Paso 1: Paleta base en `tokens.css`:** Implementar según sección
  3.1, verificando y documentando contraste AA real para cada par
  texto/fondo en ambos modos (no solo copiar los valores propuestos sin
  verificar). Agregar las variables RGB auxiliares necesarias para
  glow/translúcidos (sección 3.2/3.5).
- [ ] **Paso 2: `chartColors.ts`:** Actualizar según sección 3.6.
- [ ] **Paso 3: Header con glassmorphism:** Según sección 3.3.
- [ ] **Paso 4: `RunAnalysisButton` con glow:** Según sección 3.2.
- [ ] **Paso 5: `StatCard`/`Badge`/`DetailField` con bordes/pills
  translúcidos:** Según secciones "En Alcance" y 3.5.
- [ ] **Paso 6: Tablas responsivas (cards en mobile):** Según sección
  3.4 — el paso más grande, verificar visualmente en al menos 3
  viewports (`xs`, `md`, `fhd`) antes de dar por terminado.
- [ ] **Paso 7: Validación:** `pnpm build`, `pnpm lint`, `pnpm test` en
  verde (TODOS los tests heredados, sin modificarlos salvo que
  realmente dependan de una clase CSS específica). Verificación visual
  manual completa en navegador contra el backend real corriendo, en
  ambos modos de tema y al menos 3 viewports.

---

## 6. Verificación y Checklist de Salida (Pipeline de 5 Pasos)

- [ ] **1. Validación Arquitectónica:**
  - Cero cambios de lógica/comportamiento — solo CSS (y los `.tsx`
    mínimos de `data-label` si se usó la técnica (a) de la sección 3.4).
  - Cero valores hex sueltos fuera de `tokens.css`/`chartColors.ts`.
  - `specs/TASK_STATUS.md` no fue tocado.
  - `git diff` coincide únicamente con los archivos autorizados en la
    Sección 1. Cero archivos de `backend/` tocados.
- [ ] **2. Generación de Tests:**
  - No se exige cobertura nueva (este SPEC no agrega lógica) — se exige
    que TODOS los tests heredados de SPEC-005 a SPEC-010 sigan pasando
    sin modificaciones no justificadas.
- [ ] **3. Validación de Cobertura:**
  - `pnpm build`, `pnpm lint`, `pnpm test` en verde.
- [ ] **4. Documentación As-Built:**
  - Comentarios de contraste AA verificado en `tokens.css` (RN-02).
- [ ] **5. Trazabilidad y Estado:**
  - Checklist de este SPEC completado. **La entrada en
    `specs/TASK_STATUS.md` la agregan los arquitectos, no el agente.**
