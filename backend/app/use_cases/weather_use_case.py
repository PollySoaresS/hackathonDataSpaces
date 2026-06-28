"""Caso de uso: GetWeatherRiskUseCase — ALBA data_IA"""
from app.services.weather_service import WeatherService
from app.domain.entities.weather_risk import WeatherRisk


class GetWeatherRiskUseCase:
    def __init__(self, service: WeatherService | None = None) -> None:
        self.service = service or WeatherService()

    async def execute(self, lat: float, lon: float) -> WeatherRisk:
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError(f"Coordenadas inválidas: lat={lat}, lon={lon}")
        return await self.service.get_risk(lat, lon)
