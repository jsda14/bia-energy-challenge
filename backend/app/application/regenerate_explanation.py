from app.application.dtos import AnomalyDetailDTO
from app.domain.ports.ai_explainer_port import AIExplainerPort
from app.domain.ports.anomaly_repository_port import AnomalyRepositoryPort


class RegenerateExplanationUseCase:
    """Pide una explicación nueva en lenguaje natural para una anomalía YA
    DETECTADA, sin re-correr el motor de detección ni afectar la idempotencia
    de `AnalyzeMeterUseCase`.

    Existe puramente para fines demostrativos: con idempotencia real
    activada (ver AnalyzeMeterUseCase), volver a correr `POST /ai/analyze`
    sobre el mismo dataset no genera una explicación nueva — es el
    comportamiento correcto y deseado (evita gastar presupuesto real en
    Claude para algo que ya se detectó). Este caso de uso es la única forma
    intencional de disparar una nueva llamada al AIExplainerPort para una
    anomalía puntual ya existente, sin comprometer esa protección.
    """

    def __init__(self, anomaly_repo: AnomalyRepositoryPort, explainer: AIExplainerPort) -> None:
        self.anomaly_repo = anomaly_repo
        self.explainer = explainer

    def execute(self, anomaly_id: str) -> AnomalyDetailDTO | None:
        persisted = self.anomaly_repo.get_by_id(anomaly_id)
        if not persisted:
            return None

        explanation = self.explainer.explain(persisted.record)
        self.anomaly_repo.update_explanation(anomaly_id, explanation)

        ev = persisted.record.evidence
        return AnomalyDetailDTO(
            id=persisted.id,
            meter_id=persisted.record.meter_id,
            type=persisted.record.type.value,
            severity=persisted.record.severity.value,
            confidence=persisted.record.confidence,
            reason=explanation.reason,
            recommended_action=explanation.recommended_action,
            baseline_kwh=ev.baseline_kwh,
            observed_kwh=ev.observed_kwh,
            variation_pct=ev.variation_pct,
            affected_variables=ev.affected_variables,
            correlated_event=ev.correlated_event,
            window_start=ev.window_start,
            window_end=ev.window_end,
        )
