"""Servicio Meteorológico — ALBA data_IA"""
from app.domain.ports.weather_port import WeatherPort
from app.infrastructure.adapters.aemet_adapter import AemetAdapter
from app.domain.entities.weather_risk import WeatherRisk, WeatherObservation


class WeatherService:
    def __init__(self, port: WeatherPort | None = None) -> None:
        self.port: WeatherPort = port or AemetAdapter()

    async def get_observation(self, lat: float, lon: float) -> WeatherObservation:
        return await self.port.get_weather(lat, lon)

    async def get_risk(self, lat: float, lon: float) -> WeatherRisk:
        return await self.port.get_weather_risk(lat, lon)
