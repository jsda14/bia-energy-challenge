# Bia Energy — AI Energy Management Platform

MVP para gestionar 12 medidores eléctricos y usar IA para detectar,
explicar, priorizar y recomendar acciones sobre anomalías, sobre un
dataset real de 4.032 lecturas en 14 días (consumo, voltaje,
corriente, factor de potencia).

Backend en Python/FastAPI con arquitectura hexagonal, frontend en
React/TypeScript, motor de detección de anomalías determinista
(baseline por franja horaria + reglas de clasificación), y un
adaptador de IA que usa Claude (SDK oficial de Anthropic, tool-use
nativo) para generar explicaciones y recomendaciones en lenguaje
natural con evidencia real, cayendo a un fallback determinista si la
IA no está disponible.

## Arranque rápido

### Requisitos

- Python 3.11+
- Node.js 20+ y [pnpm](https://pnpm.io/)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

# Sembrar la base de datos con el dataset real (readings.csv/events.csv en la raíz)
python -m scripts.seed_data

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend disponible en `http://localhost:8000` (docs interactivas en
`http://localhost:8000/docs`).

**IA real (opcional):** copiar `backend/.env.example` a `backend/.env`
y completar `BIA_ANTHROPIC_API_KEY` con una API key de Anthropic. Sin
ella, el sistema funciona igual — las explicaciones caen
automáticamente a un adaptador determinista basado en plantillas
(`TemplateExplainerAdapter`), sin romper ningún flujo.

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Frontend disponible en `http://localhost:5173`.

## Tests

```bash
# Backend
cd backend && python -m pytest

# Frontend
cd frontend && pnpm test && pnpm lint && pnpm build
```

## Arquitectura

- **Backend:** arquitectura hexagonal (`domain/` → `application/` →
  `adapters/{inbound,outbound}`) — el motor de detección de anomalías
  y las reglas de negocio no tienen ninguna dependencia de
  FastAPI/SQLAlchemy/Anthropic, solo de `Ports` (`Protocol` de
  Python) que la infraestructura implementa.
- **Frontend:** capas por responsabilidad (`domain/` → `api/` →
  `stores/` → `components/{ui,feature}` → `pages/`), CSS Modules con
  convención BEM estricta, sin frameworks de utilidades CSS.
- **IA:** `ClaudeExplainerAdapter` implementa un agentic loop con
  tool-use nativo del SDK de Anthropic (sin servidor MCP separado) —
  Claude puede consultar eventos operativos reales antes de generar
  su explicación final estructurada.
- **Asistente conversacional:** mismo patrón de agentic loop sobre
  tools tipadas que llaman a los casos de uso ya existentes (nunca
  SQL libre ni acceso directo a la base de datos); cualquier acción
  con efecto real (correr análisis, cambiar estado de una anomalía)
  requiere confirmación explícita del usuario antes de ejecutarse.

Ver `ARCHITECTURE.md` y `STANDARDS.md` para el detalle completo de
decisiones y convenciones del proyecto, y `specs/` para la traza
completa de Spec-Driven Development (cada `SPEC-XXX-*.md` documenta
el alcance y las decisiones de una entrega; `specs/TASK_STATUS.md` es
el índice con el historial de cada ronda de auditoría).
