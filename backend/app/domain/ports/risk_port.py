"""
Puerto DS4M Risk — ALBA data_IA
Contrato hexagonal para el motor central de riesgo compuesto.
"""
from abc import ABC, abstractmethod

from app.domain.entities.risk_score import RiskScore


class RiskPort(ABC):

    @abstractmethod
    def compute_risk(
        self,
        heat: float,
        flood: float,
        fire: float,
        co2: float,
    ) -> RiskScore:
        """
        Calcula el riesgo compuesto DS4M.
        Todos los inputs son índices normalizados 0.0–1.0.
        Retorna RiskScore con desglose de contribuciones.
        """
        raise NotImplementedError
