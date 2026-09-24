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

## 2. Backend (Python / FastAPI)

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

## 3. Frontend (React / Vite / TypeScript)

- **TypeScript estricto**: `strict: true` en `tsconfig.json`. Prohibido `any`
  salvo justificación explícita en comentario inline (`// any: <razón>`).
- **Componentes funcionales** con hooks. Sin clases de componente.
- **Estado del servidor** vs **estado de UI** separados: fetching/cache de datos
  del backend en una capa dedicada (`src/api/` + hook por recurso), no mezclado
  con estado local de formularios/filtros.
- **Naming**: componentes en `PascalCase.tsx`, hooks en `useCamelCase.ts`, resto en
  `camelCase.ts`.
- **Sin lógica de negocio duplicada del backend** (p.ej. no recalcular
  severidad/confianza en el cliente) — el frontend renderiza lo que la API ya
  clasificó.
- **Accesibilidad mínima**: elementos interactivos con roles/aria apropiados,
  contraste legible, la app debe sentirse "producto SaaS" (ver sección 21 del PDF),
  no un panel de pruebas.

## 4. Testing

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

## 5. Git / control de versiones

- Commits pequeños y descriptivos, en español o inglés consistente por PR (elegir
  uno y mantenerlo).
- Un SPEC ≈ una rama/PR cuando el flujo de trabajo lo permita.
- `data/expected_results.csv` **nunca** se commitea ni se referencia desde código
  de aplicación — está fuera del alcance del repo por diseño del reto.
- Secrets (Anthropic API key, etc.) solo vía `.env` (gitignored) + `config.py` con
  `pydantic-settings`. Nunca hardcodeados.

## 6. Documentación

- Docstrings en todo método/función pública de `domain/` y `application/` (Google o
  NumPy style, consistente en todo el repo — Google style por defecto).
- README raíz con: cómo levantar backend, cómo levantar frontend, cómo correr
  seed de datos, cómo correr tests, y guion sugerido para la demo de 5-10 min.
- Cada SPEC completado deja su checklist marcado y una entrada en
  `specs/TASK_STATUS.md`.

## 7. Principios generales (aplican a todo el repo)

- No instalar dependencias no autorizadas explícitamente en la sección 2 del SPEC
  activo.
- No agregar endpoints, campos o métodos públicos fuera de los contratos definidos
  en la sección 3 del SPEC activo.
- No añadir abstracciones, feature flags o "por si acaso" no pedidos — YAGNI.
- No hay lógica de negocio en el LLM: el LLM explica y recomienda en lenguaje
  natural sobre hechos ya calculados por el dominio; nunca decide si algo es
  anomalía, ni su severidad, ni su confianza.
