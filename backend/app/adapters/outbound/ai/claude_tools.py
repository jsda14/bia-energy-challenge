from app.domain.ports.event_repository_port import EventRepositoryPort

GET_EVENTS_TOOL_SCHEMA = {
    "name": "get_events",
    "description": "Fetch operational events for the meter.",
    "input_schema": {
        "type": "object",
        "properties": {
            "meter_id": {"type": "string", "description": "The meter ID"}
        },
        "required": ["meter_id"],
    },
}

SUBMIT_EXPLANATION_TOOL_SCHEMA = {
    "name": "submit_explanation",
    "description": "Submit the final explanation.",
    "input_schema": {
        "type": "object",
        "properties": {
            "reason": {"type": "string"},
            "recommended_action": {"type": "string"}
        },
        "required": ["reason", "recommended_action"],
    },
}

def execute_get_events_tool(repo: EventRepositoryPort, meter_id: str) -> list[dict]:
    """Recupera los eventos operativos para un medidor y los retorna como un arreglo de diccionarios.

    Args:
        repo: Repositorio de eventos inyectado.
        meter_id: El identificador del medidor a consultar.

    Returns:
        Una lista de diccionarios con la fecha, tipo y descripciÃ³n de los eventos.
    """
    events = repo.get_by_meter_id(meter_id)
    return [
        {
            "event_timestamp": e.event_timestamp.isoformat(),
            "event_type": e.event_type.value,
            "description": e.description
        } for e in events
    ]
