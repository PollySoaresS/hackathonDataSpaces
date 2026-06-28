"""
Caso de uso: ComputeRiskUseCase — ALBA data_IA

Orquesta los motores Weather + Climate → DS4M RiskScore.
Dos modos de uso:
  1. directo: pasar heat/flood/fire/co2 ya calculados
  2. por coordenadas: el caso de uso obtiene los índices automáticamente
"""
from __future__ import annotations

from app.services.risk_service import RiskService
from app.services.climate_service import ClimateService
from app.services.weather_service import WeatherService
from app.domain.entities.risk_score import RiskScore


class ComputeRiskUseCase:
    def __init__(
        self,
        risk_service: RiskService | None = None,
        climate_service: ClimateService | None = None,
        weather_service: WeatherService | None = None,
    ) -> None:
        self.risk_svc    = risk_service    or RiskService()
        self.climate_svc = climate_service or ClimateService()
        self.weather_svc = weather_service or WeatherService()

    def compute_direct(
        self,
        heat: float,
        flood: float,
        fire: float,
        co2: float,
    ) -> RiskScore:
        """Cálculo directo con índices ya conocidos. Síncrono. Sin red."""
        return self.risk_svc.compute_risk(heat, flood, fire, co2)

    async def compute_for_location(
        self,
        lat: float,
        lon: float,
        co2_index: float = 0.0,
    ) -> RiskScore:
        """
        Cálculo completo para un punto geográfico.
        Obtiene heat+fire+flood de ClimateService (Copernicus IDW)
        y enriquece con el heat_risk operativo de WeatherService (AEMET).
        co2_index: proporción de emisiones actuales vs baseline (0.0-1.0).
        """
        climate = await self.climate_svc.get_risk(lat, lon)
        weather = await self.weather_svc.get_risk(lat, lon)

        # Combinar heat climático (estático largo plazo) con heat operativo (AEMET)
        # 70% climático + 30% operativo = índice blended
        heat_blended = 0.70 * climate.heat_index + 0.30 * weather.heat_risk

        return self.risk_svc.compute_risk(
            heat=heat_blended,
            flood=climate.flood_risk,
            fire=climate.fire_risk,
            co2=co2_index,
        )
