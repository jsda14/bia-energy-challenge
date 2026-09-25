import pytest
from datetime import datetime
from app.domain.models.anomaly import AnomalyRecord, AnomalyType, Severity, AnomalyEvidence
from app.adapters.outbound.ai.template_explainer_adapter import TemplateExplainerAdapter

def test_explain_real_anomaly():
    explainer = TemplateExplainerAdapter()
    evidence = AnomalyEvidence(
        baseline_kwh=100.0,
        observed_kwh=150.0,
        variation_pct=50.0,
        affected_variables=["consumption_kwh"],
        correlated_event=None,
        window_start=datetime(2026, 1, 1),
        window_end=datetime(2026, 1, 2),
    )
    anomaly = AnomalyRecord(
        meter_id="M-101",
        detected_at=datetime.utcnow(),
        type=AnomalyType.REAL_ANOMALY,
        severity=Severity.HIGH,
        confidence=0.9,
        evidence=evidence,
    )
    explanation = explainer.explain(anomaly)
    assert "+50.0%" in explanation.reason
    assert "consumption_kwh" in explanation.reason
    assert "No hay evento" in explanation.reason
    assert "físicamente" in explanation.recommended_action

def test_explain_explainable_anomaly():
    explainer = TemplateExplainerAdapter()
    evidence = AnomalyEvidence(
        baseline_kwh=100.0,
        observed_kwh=150.0,
        variation_pct=50.0,
        affected_variables=["consumption_kwh"],
        correlated_event="Mantenimiento",
        window_start=datetime(2026, 1, 1),
        window_end=datetime(2026, 1, 2),
    )
    anomaly = AnomalyRecord(
        meter_id="M-101",
        detected_at=datetime.utcnow(),
        type=AnomalyType.EXPLAINABLE_ANOMALY,
        severity=Severity.MEDIUM,
        confidence=0.9,
        evidence=evidence,
    )
    explanation = explainer.explain(anomaly)
    assert "Mantenimiento" in explanation.reason
    assert "Validar que el cambio" in explanation.recommended_action

def test_explain_false_positive():
    explainer = TemplateExplainerAdapter()
    evidence = AnomalyEvidence(
        baseline_kwh=100.0,
        observed_kwh=110.0,
        variation_pct=10.0,
        affected_variables=["consumption_kwh"],
        correlated_event="Corte",
        window_start=datetime(2026, 1, 1),
        window_end=datetime(2026, 1, 2),
    )
    anomaly = AnomalyRecord(
        meter_id="M-101",
        detected_at=datetime.utcnow(),
        type=AnomalyType.FALSE_POSITIVE,
        severity=Severity.LOW,
        confidence=0.9,
        evidence=evidence,
    )
    explanation = explainer.explain(anomaly)
    assert "Corte" in explanation.reason
    assert "No escalar" in explanation.recommended_action

def test_explain_data_quality():
    explainer = TemplateExplainerAdapter()
    evidence = AnomalyEvidence(
        baseline_kwh=100.0,
        observed_kwh=100.0,
        variation_pct=0.0,
        affected_variables=["power_factor"],
        correlated_event=None,
        window_start=datetime(2026, 1, 1),
        window_end=datetime(2026, 1, 2),
    )
    anomaly = AnomalyRecord(
        meter_id="M-101",
        detected_at=datetime.utcnow(),
        type=AnomalyType.DATA_QUALITY,
        severity=Severity.HIGH,
        confidence=0.9,
        evidence=evidence,
    )
    explanation = explainer.explain(anomaly)
    assert "power_factor" in explanation.reason
    assert "calibrar el sensor" in explanation.recommended_action


def test_explain_source_is_template():
    """TemplateExplainerAdapter nunca produce texto real de IA — source
    debe ser siempre 'template', nunca 'ai', sin importar el tipo de
    anomalía."""
    explainer = TemplateExplainerAdapter()
    evidence = AnomalyEvidence(
        baseline_kwh=100.0,
        observed_kwh=150.0,
        variation_pct=50.0,
        affected_variables=["consumption_kwh"],
        correlated_event=None,
        window_start=datetime(2026, 1, 1),
        window_end=datetime(2026, 1, 2),
    )
    anomaly = AnomalyRecord(
        meter_id="M-101",
        detected_at=datetime.utcnow(),
        type=AnomalyType.REAL_ANOMALY,
        severity=Severity.HIGH,
        confidence=0.9,
        evidence=evidence,
    )
    explanation = explainer.explain(anomaly)
    assert explanation.source == "template"
