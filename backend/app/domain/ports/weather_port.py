"""
Puerto Meteorológico — ALBA data_IA
Contrato hexagonal para meteorología operativa.
Desacopla casos de uso de AEMET / httpx / JSON.
"""
from abc import ABC, abstractmethod

from app.domain.entities.weather_risk import WeatherRisk, WeatherObservation


class WeatherPort(ABC):

    @abstractmethod
    async def get_weather(self, lat: float, lon: float) -> WeatherObservation:
        """Observación actual de la estación más próxima al punto."""
        raise NotImplementedError

    @abstractmethod
    async def get_weather_risk(self, lat: float, lon: float) -> WeatherRisk:
        """Observación + riesgo calculado deterministamente."""
        raise NotImplementedError
