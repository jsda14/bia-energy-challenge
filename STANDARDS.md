# STANDARDS.md — Bia Energy Challenge

Reglas vinculantes para todo código generado en este repositorio, humano o agente.
Cualquier SPEC bajo `specs/` hereda estas reglas salvo excepción explícita en la
sección 2 de ese SPEC.

## 1. Metodología: Spec-Driven Development (SDD)

- Ninguna funcionalidad se implementa sin un SPEC aprobado en `specs/`.
- El SPEC es la única fuente de verdad de contratos (DTOs, firmas, endpoints). El
  código no puede introducir campos, métodos públicos o endpoints fuera de lo
  descrito en la sección 3 del SPEC correspondiente.
- Todo SPEC se ejecuta en el orden secuencial de su sección 5 (Plan de Ejecución).
  Si un paso está bloqueado, se detiene y se pide aclaración — no se improvisa.
- Al terminar un SPEC se actualiza `specs/TASK_STATUS.md` con su estado.

## 2. Protocolo de Fronteras (Boundary Protocol) para agentes codificadores

Las instrucciones negativas sueltas ("no toques X", "detente y pregunta") se
degradan cuando el agente entra en un bucle de resolución autónoma — su
propio razonamiento termina justificando saltarse la regla "para no romper
el build". Esto ya ocurrió repetidamente en este proyecto (SPEC-001,
retrabajo #1: el agente inventó una regla de reclasificación no pedida en
vez de detenerse; auditoría #6: modificó umbrales de RN-06 sin autorización;
SPEC-002: agregó un parámetro no contractual a la firma de un método de un
puerto, dentro de un archivo que SÍ estaba autorizado a crear, y declaró en
su propia FASE 0 que no había fronteras violadas). Por eso, todo agente
codificador que ejecute un SPEC de este repo sigue este protocolo de dos
fases, obligatorio y sin excepción:

**FASE 0 — Declaración de fronteras (dry-run, antes de escribir código):**
1. Antes de crear o editar cualquier archivo, lista explícitamente qué
   archivos vas a tocar, cotejándolos uno por uno contra la lista de
   "Archivos Afectados" (sección 1) del SPEC activo.
2. Si algún archivo que crees necesario tocar NO está en esa lista (o está
   explícitamente en "Prohibido modificar"), **no lo edites**. Emite
   únicamente esta salida de texto y termina el turno ahí:

   ```
   BLOCKED_BY_BOUNDARY: <archivo> — <razón por la que crees que hace falta tocarlo>
   ```

   Esto aplica igual si la razón es "si no lo toco, el build/test falla" —
   ese es exactamente el caso que este protocolo existe para atrapar. Emitir
   `BLOCKED_BY_BOUNDARY` es una salida válida y exitosa del turno, no un
   fracaso — no sigas intentando resolverlo con otra herramienta ni asumas
   que el usuario "seguro querría" que lo arregles.
3. **La frontera no es solo QUÉ archivo tocas — es también QUÉ CONTRATO
   implementas dentro de él.** Estar autorizado a crear/modificar un archivo
   (sección 1 del SPEC) no autoriza a desviarte de las firmas, campos o
   comportamientos exactos definidos en la sección 3 ("Contratos e
   Interfaces") de ese mismo SPEC. Antes de pasar a FASE 1, coteja también
   cada firma de método/función que vayas a escribir contra su definición
   literal en la sección 3. Si necesitas un parámetro, campo, valor de
   retorno o comportamiento que la sección 3 no contempla — así sea un
   default opcional que "no rompe nada" — es la MISMA condición de
   `BLOCKED_BY_BOUNDARY` que un archivo fuera de alcance. No lo agregues por
   tu cuenta asumiendo que es una mejora razonable.
4. Solo si el 100% de los archivos Y el 100% de las firmas declaradas caen
   dentro de lo autorizado, pasa a FASE 1.

**FASE 1 — Ejecución (solo si FASE 0 no emitió ningún `BLOCKED_BY_BOUNDARY`):**
- Procede con las tareas de la sección 5 del SPEC en orden secuencial, como
  ya indica la sección 1 de este documento.
- Si a mitad de la implementación descubres que hace falta tocar un archivo
  no declarado en la Fase 0 (un descubrimiento nuevo, no visible al inicio),
  vuelve a aplicar el mismo protocolo: emite `BLOCKED_BY_BOUNDARY` para ese
  archivo específico y detente ahí, no continúes editando otros archivos
  mientras esperas resolución.

Esto no reemplaza las instrucciones "no toques X" que ya aparecen en cada
SPEC — las refuerza dándoles una salida estructurada y nombrada, más difícil
de saltarse en un bucle de tool-calling que una prohibición en prosa.

## 3. Backend (Python / FastAPI)

- **Versión**: Python 3.11+.
- **Estilo**: PEP 8, type hints obligatorios en toda función pública. `pydantic`
  para DTOs/schemas de entrada y salida de la API y para value objects del dominio
  que lo requieran.
- **Formateo/lint**: `black` + `ruff` (line length 100). Sin excepciones de estilo
  ad-hoc en el código.
- **Arquitectura hexagonal** (ver `ARCHITECTURE.md`):
  - `domain/` no importa nada de `adapters/` ni `application/`. Cero dependencias a
    FastAPI, SQLAlchemy o el SDK de Anthropic dentro de `domain/`.
  - `application/` depende de `domain/` y de *puertos* (`Protocol`/ABC), nunca de
    adapters concretos — la inyección de dependencias concretas ocurre en el
    composition root (`main.py`).
  - Los adapters outbound (`persistence/`, `ai/`) implementan los puertos definidos
    en `domain/ports/`.
- **Errores**: excepciones de dominio propias (`DomainError` y subclases), nunca
  `Exception` genérica atrapada silenciosamente. La capa API traduce excepciones de
  dominio a códigos HTTP apropiados (400/404/422/500) en un exception handler
  central, no en cada endpoint.
- **Naming**: `snake_case` para funciones/variables, `PascalCase` para clases,
  módulos en `snake_case`.
- **Nada de lógica de negocio en routers FastAPI** — un router solo
  parsea/valida input, llama un caso de uso, serializa output.

## 4. Frontend (React / Vite / TypeScript)

### 4.1 Stack y gestor de paquetes

- **Gestor de paquetes**: `pnpm` — no `npm` ni `yarn`. `pnpm-lock.yaml` se
  commitea, nunca `package-lock.json` ni `yarn.lock`.
- **Build**: Vite. **TypeScript estricto**: `strict: true` en
  `tsconfig.json`. Prohibido `any` salvo justificación explícita en
  comentario inline (`// any: <razón>`).
- **Componentes funcionales** con hooks. Sin clases de componente.
- **Routing**: React Router. Rutas declarativas por recurso
  (`/meters`, `/meters/:meterId`, `/anomalies`, `/anomalies/:id`) — nunca
  un switch manual de "página activa" en estado local; la URL es la fuente
  de verdad de qué se está viendo, para soportar botón atrás del navegador
  y deep-linking.
- **Estado de servidor**: TanStack Query (React Query) para todo fetching a
  la API del backend — cache, loading/error states, y el patrón de
  invalidación/refetch tras `POST /ai/analyze`. Nunca `fetch` +
  `useState`/`useEffect` a mano para datos del servidor.
- **Estado de cliente global**: Zustand, solo para estado de UI genuinamente
  compartido entre pantallas/componentes no relacionados por props (ej.
  filtros/orden de la tabla de medidores si se preservan al navegar,
  estado visible globalmente de "análisis en curso" tras disparar
  `POST /ai/analyze`, notificaciones/toasts). Redux queda descartado por
  completo — demasiado boilerplate (actions/reducers/store/dispatch) para
  este alcance, sin que aporte nada que Zustand no resuelva más simple.
  Estado local de un solo componente (un input, un toggle) sigue siendo
  `useState` normal — Zustand es solo para lo que de verdad cruza
  fronteras de componentes no emparentados.
- **Regla de separación** (las tres piezas de estado nunca se mezclan):
  - **Estado de servidor** (datos del backend) → TanStack Query.
  - **Estado de cliente compartido** (UI global) → Zustand.
  - **Estado de UI local** (un componente, no compartido) → `useState`.
  Un store de Zustand nunca cachea datos que ya vienen de TanStack Query
  (eso duplicaría la fuente de verdad) — solo guarda estado que no viene
  del servidor.
- **Naming**: componentes en `PascalCase.tsx`, hooks en `useCamelCase.ts`,
  resto en `camelCase.ts`.
- **Sin lógica de negocio duplicada del backend** (p.ej. no recalcular
  severidad/confianza en el cliente) — el frontend renderiza lo que la API
  ya clasificó.
- **Accesibilidad mínima**: elementos interactivos con roles/aria
  apropiados, contraste legible, la app debe sentirse "producto SaaS" (ver
  sección 21 del PDF), no un panel de pruebas.
- **Testing (dependencias autorizadas desde SPEC-007, ver sección 5)**:
  `vitest`, `@testing-library/react`, `@testing-library/jest-dom`,
  `@testing-library/user-event`, `jsdom` (entorno de test de Vitest). No
  agregar Cypress/Playwright ni otro runner de e2e navegador-real — fuera
  de alcance de este proyecto.

### 4.2 Validación de datos: Zod, a mano, fuente única de verdad en frontend

- Cada Response schema del backend (`DashboardSummaryResponse`,
  `MeterSummaryResponse`, `AnomalyDetailResponse`, etc. — ya definidos
  exactos en SPEC-003) se replica como un schema `zod` en
  `frontend/src/api/schemas.ts`. El tipo TypeScript se infiere del propio
  schema (`z.infer<typeof X>`), nunca se escribe una interfaz duplicada a
  mano por separado.
- Toda respuesta de la API se parsea con su schema Zod antes de usarse en
  un componente (`schema.parse(response.data)`, nunca `as Tipo` para
  forzar un cast sin validar). Si el backend cambia y rompe el contrato,
  el frontend lo detecta al parsear, no de forma silenciosa en producción.
- Prohibido generar tipos automáticamente desde OpenAPI
  (`openapi-typescript` u otra herramienta de codegen) — decisión
  deliberada para no depender de un paso de build adicional ni de tener el
  backend levantado para generar tipos, dado el alcance de este MVP.

### 4.3 Estilos: CSS Modules + BEM estricto, sin frameworks de utilidades

- **Prohibido Tailwind, Bootstrap, Material UI, Chakra, o cualquier
  framework de componentes/utilidades pre-estilados.** Decisión
  deliberada: se busca un diseño visual propio, no reconocible como "hecho
  con un framework de IA por defecto".
- **CSS Modules** (`Componente.module.css`, uno por componente) +
  **convención BEM estricta** dentro de cada módulo:
  `.bloque`, `.bloque__elemento`, `.bloque__elemento--modificador`. El
  "bloque" es el nombre del componente en kebab-case (ej. componente
  `MeterCard` → clases `.meter-card`, `.meter-card__header`,
  `.meter-card__header--critical`).
- **Tokens de diseño** en variables CSS globales (`src/styles/tokens.css`):
  paleta de color, espaciado, tipografía, radios, sombras — nunca colores o
  medidas "mágicas" hardcodeadas dentro de un módulo de componente. Todo
  módulo de componente consume `var(--token-x)`, nunca un valor literal
  repetido.
- **Nada de estilos inline** (`style={{...}}`) salvo un valor
  verdaderamente dinámico calculado en runtime (ej. el ancho de una barra
  de progreso) — y aun así, preferir una CSS custom property inyectada
  (`style={{ '--progress': pct }}`) consumida desde el CSS Module, no
  propiedades de layout/color hardcodeadas inline.
- El diseño visual (paleta, tipografía, jerarquía, "personalidad" de la
  UI) se define en el SPEC de frontend correspondiente, no en este
  documento — este documento fija la convención técnica (BEM + CSS
  Modules + tokens), no los valores de diseño en sí.

### 4.4 Mobile-first y breakpoints

- Todo CSS se escribe **mobile-first**: los estilos base (sin media query)
  son los del viewport más angosto; cada `@media (min-width: ...)` añade o
  sobreescribe para viewports más anchos. Nunca al revés
  (`max-width` como base con excepciones hacia abajo).
- **Breakpoints fijos** (variables CSS + constantes TS si hace falta
  lógica de layout en JS, nunca un valor de breakpoint hardcodeado suelto
  en un componente):

  | Nombre | Ancho mínimo | Uso típico |
  |---|---|---|
  | `xs` | 480px | móvil grande / phablet |
  | `sm` | 640px | móvil horizontal |
  | `md` | 768px | tablet |
  | `lg` | 1024px | tablet horizontal / laptop pequeña |
  | `laptop` | 1366px | laptop estándar |
  | `xl` | 1440px | desktop |
  | `fhd` | 1920px | monitor Full HD |
  | `qhd` | 2560px | monitor 2K/QHD |

- Layouts de datos densos (tablas de medidores, grillas de KPIs) deben
  aprovechar el espacio extra en `laptop`/`xl`/`fhd`/`qhd` (más columnas,
  paneles side-by-side) en vez de simplemente centrar contenido con
  márgenes vacíos crecientes — es un dashboard de datos, no un blog.

## 5. Testing

- **Backend**: `pytest`. Estructura en tres niveles:
  - `tests/unit/` — dominio puro, sin IO, sin DB, sin red. Cubre RN-* y CB-* de cada
    SPEC.
  - `tests/integration/` — repos concretos contra SQLite (en memoria o archivo
    temporal), sin mockear la DB.
  - `tests/e2e/` — `TestClient` de FastAPI contra la app completa con DB de test.
- **Cobertura mínima**: 85% en código nuevo de dominio/aplicación (no aplica a
  adapters triviales de infraestructura).
- **El motor de detección de anomalías debe tener tests explícitos por caso del
  dataset**: M-109 (real), M-104 (explicable), M-106 (falso positivo), M-112
  (calidad de datos) — usando fixtures derivadas de `readings.csv`/`events.csv`,
  nunca de `expected_results.csv` (no disponible ni debe estarlo).
- **Frontend**: `Vitest` + `@testing-library/react`. SPEC-005 (fundación,
  sin componentes de negocio) y SPEC-006 (Dashboard + Meter List, primera
  entrega con lógica real) quedaron sin tests automatizados por decisión
  explícita — deuda aceptada y cerrada, no se exige cobertura retroactiva
  sobre esas dos SPECs. **A partir de SPEC-007 inclusive**, toda SPEC de
  frontend que implemente lógica no trivial (ordenamiento, filtrado,
  formateo condicional, manejo de estados de error/carga, reglas de
  negocio RN-*/CB-* propias de esa página) debe incluir su propia
  cobertura de Vitest + Testing Library dentro del mismo SPEC, en la
  sección 5 (Plan de Ejecución) — mismo criterio que el backend: tests
  desde que existe lógica real que probar, no una SPEC de testing
  retroactiva al final del proyecto.
  - Prioridad de cobertura: `domain/` (funciones puras, fácil de testear
    exhaustivamente) > lógica de componentes de `components/feature/`
    (sort, filtro, casos borde) > páginas (`pages/`, smoke test de que
    renderiza sin crashear en cada estado: loading/error/vacío/con datos).
  - No se exige cobertura de `components/ui/` puramente presentacionales
    (`Badge`, `StatCard`) salvo que tengan lógica condicional propia más
    allá de mapear props a clases CSS.
- **Frontend**: tests de componentes críticos (Dashboard, MeterDetail, Anomalies)
  con Vitest + Testing Library, a nivel de comportamiento (qué ve el usuario), no
  de implementación interna.
- **IA/Claude**: el `AIExplainerPort` se testea con un adapter mock/fake en
  unit/integration — nunca se llama a la API real de Anthropic en tests
  automatizados (evita costos y flakiness). Un test manual/documentado puede
  validar el adapter real por separado.
- El agentic loop del `ClaudeExplainerAdapter` se testea con un `EventQueryTool`
  mock — nunca se llama al MCP real ni a la API de Anthropic en tests
  automatizados.

## 6. Git / control de versiones

- Commits pequeños y descriptivos, en español o inglés consistente por PR (elegir
  uno y mantenerlo).
- Un SPEC ≈ una rama/PR cuando el flujo de trabajo lo permita.
- `data/expected_results.csv` **nunca** se commitea ni se referencia desde código
  de aplicación — está fuera del alcance del repo por diseño del reto.
- Secrets (Anthropic API key, etc.) solo vía `.env` (gitignored) + `config.py` con
  `pydantic-settings`. Nunca hardcodeados.

## 7. Documentación

- Docstrings en todo método/función pública de `domain/` y `application/` (Google o
  NumPy style, consistente en todo el repo — Google style por defecto).
- README raíz con: cómo levantar backend, cómo levantar frontend, cómo correr
  seed de datos, cómo correr tests, y guion sugerido para la demo de 5-10 min.
- Cada SPEC completado deja su checklist marcado y una entrada en
  `specs/TASK_STATUS.md`.

## 8. Principios generales (aplican a todo el repo)

- No instalar dependencias no autorizadas explícitamente en la sección 2 del SPEC
  activo.
- No agregar endpoints, campos o métodos públicos fuera de los contratos definidos
  en la sección 3 del SPEC activo.
- No añadir abstracciones, feature flags o "por si acaso" no pedidos — YAGNI.
- No hay lógica de negocio en el LLM: el LLM explica y recomienda en lenguaje
  natural sobre hechos ya calculados por el dominio; nunca decide si algo es
  anomalía, ni su severidad, ni su confianza.
