"""Schemas de tools y funciones ejecutoras para el asistente conversacional
(SPEC-013). Mismo estilo que `claude_tools.py`: las tools de solo lectura
tienen una función ejecutora aquí; las tools con side-effect
(`run_analysis`, `set_triage_status`) NO la tienen — nunca se ejecutan
dentro del loop del adapter sin confirmación explícita del usuario (ver
`ClaudeAssistantAdapter`)."""

from dataclasses import asdict

from app.application.list_anomalies import ListAnomaliesUseCase
from app.application.get_meter_detail import GetMeterDetailUseCase
from app.application.get_dashboard_summary import GetDashboardSummaryUseCase

GET_ANOMALIES_TOOL_SCHEMA = {
    "name": "get_anomalies",
    "description": "List detected anomalies, optionally filtered by severity and/or meter_id.",
    "input_schema": {
        "type": "object",
        "properties": {
            "severity": {"type": ["string", "null"], "description": "LOW, MEDIUM or HIGH. Omit or null for all."},
            "meter_id": {"type": ["string", "null"], "description": "Filter by a specific meter. Omit or null for all."},
        },
    },
}

GET_METER_DETAIL_TOOL_SCHEMA = {
    "name": "get_meter_detail",
    "description": "Get detail (consumption, status, readings, events) for a specific meter.",
    "input_schema": {
        "type": "object",
        "properties": {
            "meter_id": {"type": "string", "description": "The meter ID"},
        },
        "required": ["meter_id"],
    },
}

GET_DASHBOARD_SUMMARY_TOOL_SCHEMA = {
    "name": "get_dashboard_summary",
    "description": "Get the overall dashboard summary (anomalies detected, high priority count, average confidence, last analysis time).",
    "input_schema": {"type": "object", "properties": {}},
}

# Tools con side-effect: solo se declara el schema para que el modelo pueda
# *proponerlas*. Nunca tienen función ejecutora en este archivo — su
# ejecución real ocurre exclusivamente en ClaudeAssistantAdapter, y solo
# tras `pending_confirmation == {"confirmed": True}` explícito del usuario.

RUN_ANALYSIS_TOOL_SCHEMA = {
    "name": "run_analysis",
    "description": "Run anomaly analysis for a specific meter, or all meters if meter_id is omitted. REQUIRES explicit user confirmation before executing — never call this expecting it to run immediately, it will only propose the action.",
    "input_schema": {
        "type": "object",
        "properties": {
            "meter_id": {"type": ["string", "null"], "description": "Meter to analyze, or null for all meters."},
        },
    },
}

SET_TRIAGE_STATUS_TOOL_SCHEMA = {
    "name": "set_triage_status",
    "description": "Set the triage status (NEW, ACKNOWLEDGED or DISMISSED) of an anomaly. REQUIRES explicit user confirmation before executing — never call this expecting it to run immediately, it will only propose the action.",
    "input_schema": {
        "type": "object",
        "properties": {
            "anomaly_id": {"type": "string"},
            "status": {"type": "string", "enum": ["NEW", "ACKNOWLEDGED", "DISMISSED"]},
        },
        "required": ["anomaly_id", "status"],
    },
}

ALL_TOOL_SCHEMAS = [
    GET_ANOMALIES_TOOL_SCHEMA,
    GET_METER_DETAIL_TOOL_SCHEMA,
    GET_DASHBOARD_SUMMARY_TOOL_SCHEMA,
    RUN_ANALYSIS_TOOL_SCHEMA,
    SET_TRIAGE_STATUS_TOOL_SCHEMA,
]


def execute_get_anomalies_tool(
    use_case: ListAnomaliesUseCase, severity: str | None, meter_id: str | None
) -> list[dict]:
    """Lista anomalías vía ListAnomaliesUseCase (ya existente), filtrando
    por severity en Python plano sobre el resultado — ListAnomaliesUseCase
    solo filtra por meter_id nativamente, no se le agrega un parámetro
    nuevo no autorizado por otro SPEC."""
    dtos = use_case.execute(meter_id)
    if severity:
        dtos = [d for d in dtos if d.severity == severity]
    return [asdict(d) | {"detected_at": d.detected_at.isoformat()} for d in dtos]


def execute_get_meter_detail_tool(use_case: GetMeterDetailUseCase, meter_id: str) -> dict:
    dto = use_case.execute(meter_id)
    if dto is None:
        return {"error": f"Meter '{meter_id}' not found"}
    return {
        "meter_id": dto.meter_id,
        "name": dto.name,
        "location": dto.location,
        "status": dto.status,
        "consumption_kwh": dto.consumption_kwh,
        "baseline_kwh": dto.baseline_kwh,
        "variation_pct": dto.variation_pct,
        # Se omiten readings/events crudos del payload de la tool: son
        # potencialmente largos y no aportan a una respuesta conversacional
        # de resumen; el asistente puede volver a llamar get_anomalies para
        # detalle de anomalías si hace falta.
    }


def execute_get_dashboard_summary_tool(use_case: GetDashboardSummaryUseCase) -> dict:
    dto = use_case.execute()
    return {
        "anomalies_detected": dto.anomalies_detected,
        "high_priority_count": dto.high_priority_count,
        "average_confidence": dto.average_confidence,
        "last_analysis_at": dto.last_analysis_at.isoformat() if dto.last_analysis_at else None,
    }
