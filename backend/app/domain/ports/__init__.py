"""Módulo de puertos de la capa de dominio."""

from app.domain.ports.ai_explainer_port import AIExplainerPort, AIExplanation
from app.domain.ports.event_repository_port import EventRepositoryPort
from app.domain.ports.meter_repository_port import MeterRepositoryPort
from app.domain.ports.reading_repository_port import ReadingRepositoryPort

__all__ = [
    "AIExplainerPort",
    "AIExplanation",
    "EventRepositoryPort",
    "MeterRepositoryPort",
    "ReadingRepositoryPort",
]

