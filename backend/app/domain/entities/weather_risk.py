"""
Entidad de dominio — WeatherRisk
Datos meteorológicos operativos + nivel de riesgo calculado deterministicamente.
Fuente AEMET OpenData. Sin IA para el cálculo.
"""
from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class WeatherObservation:
    """Observación en crudo de la estación más próxima."""
    station_id: str
    station_name: str
    lat: float
    lon: float
    temperature: float       # °C
    humidity: float          # %
    wind_speed: float        # km/h
    precipitation: float     # mm/h acumulado en la hora actual


@dataclass(frozen=True)
class WeatherRisk:
    """Resultado enriquecido con riesgo calculado."""
    observation: WeatherObservation
    heat_risk: float          # 0.0 – 1.0
    storm_risk: float         # 0.0 – 1.0
    wind_risk: float          # 0.0 – 1.0
    risk_score: float         # 0.0 – 1.0 (suma ponderada)
    risk_level: RiskLevel     # low | medium | high

    def to_dict(self) -> dict:
        obs = self.observation
        return {
            "station": {
                "id": obs.station_id,
                "name": obs.station_name,
                "lat": obs.lat,
                "lon": obs.lon,
            },
            "conditions": {
                "temperature_c": obs.temperature,
                "humidity_pct": obs.humidity,
                "wind_speed_kmh": obs.wind_speed,
                "precipitation_mmh": obs.precipitation,
            },
            "risk": {
                "heat_risk": round(self.heat_risk, 3),
                "storm_risk": round(self.storm_risk, 3),
                "wind_risk": round(self.wind_risk, 3),
                "risk_score": round(self.risk_score, 3),
                "risk_level": self.risk_level,
            },
        }
