# TASK_STATUS.md — Índice de SPECs

Índice global de todos los SPECs del proyecto. Cada fila resume el estado de
un SPEC; el detalle granular de tareas (checklists de sección 5/6) vive
dentro del propio archivo `SPEC-XXX-*.md`. Este archivo se actualiza cada vez
que un SPEC cambia de estado (aprobado, en retrabajo, bloqueado).

| SPEC | Título | Estado | Retrabajos | Última actualización |
|---|---|---|---|---|
| [SPEC-001](SPEC-001-domain-anomaly-detection.md) | Dominio: Modelos y Motor de Detección de Anomalías | ✅ Aprobado | 5 | 2026-09-24 |
| [SPEC-002](SPEC-002-persistence-and-seed.md) | Persistencia (SQLite/SQLAlchemy) y Seed de Datos | ✅ Aprobado | 1 | 2026-09-24 |
| SPEC-003 | Casos de uso + API FastAPI | ⬜ No iniciado | — | — |
| SPEC-004 | IA — Adapter Claude (agentic loop + MCP EventQueryTool) | ⬜ No iniciado | — | — |
| SPEC-005+ | Frontend — Dashboard, Meters, Detail, Anomalies, Investigation | ⬜ No iniciado | — | — |

**Leyenda de estado:** ⬜ No iniciado · 🟡 En progreso / en retrabajo · 🔴 Bloqueado · ✅ Aprobado

---

## SPEC-001 — Dominio: Modelos y Motor de Detección de Anomalías

**Estado:** ✅ Aprobado (2026-09-24, tras 5 rondas de retrabajo y 6 auditorías).

**Resumen:** Modelos de dominio inmutables (`Meter`, `Reading`, `Event`,
`AnomalyRecord`) y motor de detección determinista (`AnomalyDetector`),
verificado contra las 4.032 lecturas reales completas del dataset. Los 4
casos documentados por el PDF (M-109, M-104, M-106, M-112) clasifican
correctamente en una sola ventana cada uno; los 8 medidores restantes dan 0
falsos positivos. 28 tests unitarios, 93% de cobertura sobre
`domain/detection/` + `domain/models/`.

**Historial de retrabajos** (motivo de cada ronda, resumido):
1. Bug de severidad en `DATA_QUALITY` (RN-06 solo miraba voltaje, no
   power_factor) + fragmentación de ventanas por bloqueo compartido entre
   fases.
2. Reordenar fases arregló M-112 pero fragmentó M-109 (power_factor
   colapsado cae en clustering eléctrico) + regla de reclasificación no
   autorizada agregada por el agente (revertida).
3. Tolerancia de gap dentro de la racha de consumo para que un valle
   nocturno normal no corte un incidente sostenido.
4. Tolerancia de gap insuficiente ante contexto real completo — descubierto
   que la variación diurna natural del dataset (47-59%) ya supera el umbral
   de spike (30%) por sí sola.
5. Rediseño de RN-01/RN-02: baseline por franja horaria (comparar cada hora
   contra su propio histórico horario) en vez de baseline plano de 24h —
   resuelve el problema de raíz para los 12 medidores a la vez.

**Lección de proceso más importante:** nunca validar con fixtures recortados
"a medida" del caso que se quiere probar — solo el histórico 100% completo
real revela interacciones con el baseline móvil. Ver `PROJECT_NOTES.md`
(bitácora personal, no versionada) para el detalle completo de cada
auditoría.

---

## SPEC-002 — Persistencia (SQLite/SQLAlchemy) y Seed de Datos

**Estado:** ✅ Aprobado (2026-09-24, 1 ronda de retrabajo).

**Resumen:** `MeterRepositoryPort`/`ReadingRepositoryPort`/
`EventRepositoryPort` como `Protocol`, implementados por adapters
SQLAlchemy que nunca exponen filas ORM fuera de `persistence/`. Script de
seed idempotente verificado corriendo dos veces contra la base de datos
real: 12 medidores, 4.032 lecturas, 4 eventos, conteos idénticos en ambas
corridas. 46 tests (28 unit heredados sin tocar + 18 integration nuevos).

**Alcance:** Solo `Meter`/`Reading`/`Event` (repos + seed desde CSV real).
`AnomalyRepositoryPort` queda para SPEC-003, cuando exista el caso de uso que
genera y persiste anomalías.

**Retrabajo (motivo):**
1. `MeterRepositoryPort.save()` se entregó con un parámetro `created_at`
   no autorizado, desviándose de la firma exacta definida en la sección 3.1
   del SPEC — descubierto en auditoría, no reportado por el propio agente
   (su declaración de Fase 0 afirmó que no había fronteras violadas). Motivó
   endurecer `STANDARDS.md` sección 2 (Boundary Protocol) para cubrir
   explícitamente firmas/contratos, no solo rutas de archivo. Fix: firma
   restaurada exacta, `created_at` resuelto con `datetime.utcnow()` dentro
   del repo en vez de recibirlo como parámetro.

**Hallazgo menor no bloqueante:** `Meter.id` se construye distinto en
`seed()` (usa el string `meter_id`) que en los métodos de lectura del repo
(usa el entero autoincremental de la tabla) — inconsistencia latente sin
consumidor real todavía. A vigilar si SPEC-003 llega a depender de
`Meter.id`.
