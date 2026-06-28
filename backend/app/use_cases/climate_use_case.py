"""Caso de uso: GetClimateRiskUseCase — ALBA data_IA"""
from app.services.climate_service import ClimateService
from app.domain.entities.climate_risk import ClimateRisk


class GetClimateRiskUseCase:
    def __init__(self, service: ClimateService | None = None) -> None:
        self.service = service or ClimateService()

    async def execute(self, lat: float, lon: float) -> ClimateRisk:
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError(f"Coordenadas inválidas: lat={lat}, lon={lon}")
        return await self.service.get_risk(lat, lon)
