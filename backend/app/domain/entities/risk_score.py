"""
Entidad de dominio — RiskScore (DS4M)
Motor central de riesgo territorial compuesto.
Fórmula determinista. Sin IA.

risk_score = heat_weight * heat
           + flood_weight * flood
           + fire_weight * fire
           + co2_weight * co2

Independiente de GIS — opera sobre índices normalizados 0.0-1.0.
"""
from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["very_low", "low", "medium", "high", "very_high"]


@dataclass(frozen=True)
class RiskScore:
    # Inputs (índices normalizados 0.0–1.0)
    heat: float
    flood: float
    fire: float
    co2: float

    # Pesos aplicados (configurables, suman 1.0)
    heat_weight: float
    flood_weight: float
    fire_weight: float
    co2_weight: float

    # Resultado
    risk_score: float     # 0.0–1.0
    risk_level: RiskLevel

    # Desglose para trazabilidad
    heat_contribution: float
    flood_contribution: float
    fire_contribution: float
    co2_contribution: float

    def to_dict(self) -> dict:
        return {
            "risk_score": round(self.risk_score, 4),
            "risk_level": self.risk_level,
            "inputs": {
                "heat": round(self.heat, 4),
                "flood": round(self.flood, 4),
                "fire": round(self.fire, 4),
                "co2": round(self.co2, 4),
            },
            "weights": {
                "heat": self.heat_weight,
                "flood": self.flood_weight,
                "fire": self.fire_weight,
                "co2": self.co2_weight,
            },
            "contributions": {
                "heat": round(self.heat_contribution, 4),
                "flood": round(self.flood_contribution, 4),
                "fire": round(self.fire_contribution, 4),
                "co2": round(self.co2_contribution, 4),
            },
        }
