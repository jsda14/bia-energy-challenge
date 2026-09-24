from app.domain.models.anomaly import AnomalyRecord, AnomalyType
from app.domain.ports.ai_explainer_port import AIExplanation, AIExplainerPort

class TemplateExplainerAdapter(AIExplainerPort):
    """Fallback determinista de AIExplainerPort: genera reason y
    recommended_action con plantillas de texto a partir de AnomalyEvidence,
    sin llamar a ningún servicio externo.
    """

    def explain(self, anomaly: AnomalyRecord) -> AIExplanation:
        t = anomaly.type
        ev = anomaly.evidence
        
        var_pct = f"{ev.variation_pct:+.1f}%" if ev.variation_pct is not None else "N/A"
        aff_vars = ", ".join(ev.affected_variables) if ev.affected_variables else "ninguna"
        corr_event = ev.correlated_event if ev.correlated_event else "ninguno"
        
        if t == AnomalyType.REAL_ANOMALY:
            reason = f"Se detectó una variación de {var_pct} en el consumo y anomalías en {aff_vars}. No hay evento operativo conocido que lo explique."
            action = "Investigar el medidor y la instalación físicamente para descartar fallas o fraude."
        elif t == AnomalyType.EXPLAINABLE_ANOMALY:
            reason = f"Se detectó una variación de {var_pct} que está correlacionada con el evento conocido: '{corr_event}'."
            action = "Validar que el cambio operativo sea el esperado, sin escalar como incidente."
        elif t == AnomalyType.FALSE_POSITIVE:
            reason = f"La desviación detectada es totalmente consistente con el evento conocido: '{corr_event}'."
            action = "No escalar. Este comportamiento es esperado bajo las condiciones actuales."
        elif t == AnomalyType.DATA_QUALITY:
            reason = f"Se detectaron inconsistencias en variables eléctricas ({aff_vars}) mientras el consumo permanece dentro de lo esperable."
            action = "Validar y calibrar el sensor o instalación de medición."
        else:
            reason = "Anomalía no clasificada."
            action = "Revisión manual."
            
        return AIExplanation(
            reason=reason,
            recommended_action=action
        )
