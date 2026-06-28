"""
Servicio DS4M Risk — ALBA data_IA

Motor central de riesgo compuesto. Lógica determinista pura.
Sin IA. Sin GIS. Sin red. Testeable en aislamiento total.

Arquitectura:
  WeatherEngine  ─┐
  ClimateEngine  ─┼──→ RiskService.compute(heat, flood, fire, co2) → RiskScore
  CO2 Metrics    ─┘

Los pesos por defecto responden al contexto climático mediterráneo CV:
  - Calor: mayor peso (verano 2024, ola histórica)
  - Inundación: segundo peso (episodio DANA 2024, L'Albufera, Vega Baja)
  - Incendio: tercero (EFFIS 2024 — Sierra Calderona, Els Ports)
  - CO2: menor peso (dato de emisiones operativas, no climático)

Los pesos son sobreescribibles en config.py → RISK_WEIGHT_*.
"""
from __future__ import annotations

from core.config import get_settings
from app.domain.ports.risk_port import RiskPort
from app.domain.entities.risk_score import RiskScore, RiskLevel

_settings = get_settings()


def _classify_level(score: float) -> RiskLevel:
    if score >= 0.80:
        return "very_high"
    if score >= 0.60:
        return "high"
    if score >= 0.40:
        return "medium"
    if score >= 0.20:
        return "low"
    return "very_low"


class RiskService(RiskPort):
    """
    Motor DS4M: suma ponderada de índices de riesgo.

    risk_score = w_heat  * heat
               + w_flood * flood
               + w_fire  * fire
               + w_co2   * co2
    """

    def __init__(
        self,
        heat_weight: float | None = None,
        flood_weight: float | None = None,
        fire_weight: float | None = None,
        co2_weight: float | None = None,
    ) -> None:
        # Cargar pesos desde config (permiten override en tests y despliegue)
        self.w_heat  = heat_weight  if heat_weight  is not None else getattr(_settings, "RISK_WEIGHT_HEAT",  0.40)
        self.w_flood = flood_weight if flood_weight is not None else getattr(_settings, "RISK_WEIGHT_FLOOD", 0.30)
        self.w_fire  = fire_weight  if fire_weight  is not None else getattr(_settings, "RISK_WEIGHT_FIRE",  0.20)
        self.w_co2   = co2_weight   if co2_weight   is not None else getattr(_settings, "RISK_WEIGHT_CO2",   0.10)

        # Normalizar pesos si no suman exactamente 1.0
        total = self.w_heat + self.w_flood + self.w_fire + self.w_co2
        if abs(total - 1.0) > 0.001:
            self.w_heat  /= total
            self.w_flood /= total
            self.w_fire  /= total
            self.w_co2   /= total

    def compute_risk(
        self,
        heat: float,
        flood: float,
        fire: float,
        co2: float,
    ) -> RiskScore:
        # Clamp inputs a [0.0, 1.0]
        heat  = min(max(heat,  0.0), 1.0)
        flood = min(max(flood, 0.0), 1.0)
        fire  = min(max(fire,  0.0), 1.0)
        co2   = min(max(co2,   0.0), 1.0)

        c_heat  = self.w_heat  * heat
        c_flood = self.w_flood * flood
        c_fire  = self.w_fire  * fire
        c_co2   = self.w_co2   * co2

        score = c_heat + c_flood + c_fire + c_co2

        return RiskScore(
            heat=heat,
            flood=flood,
            fire=fire,
            co2=co2,
            heat_weight=round(self.w_heat, 4),
            flood_weight=round(self.w_flood, 4),
            fire_weight=round(self.w_fire, 4),
            co2_weight=round(self.w_co2, 4),
            risk_score=round(min(score, 1.0), 4),
            risk_level=_classify_level(score),
            heat_contribution=round(c_heat, 4),
            flood_contribution=round(c_flood, 4),
            fire_contribution=round(c_fire, 4),
            co2_contribution=round(c_co2, 4),
        )
