"""
Puerto Climático — ALBA data_IA
Contrato hexagonal para datos climáticos territoriales.
Desacopla casos de uso del origen real (Copernicus CDS / PostGIS).
"""
from abc import ABC, abstractmethod

from app.domain.entities.climate_risk import ClimateRisk


class ClimatePort(ABC):

    @abstractmethod
    async def get_heat_index(self, lat: float, lon: float) -> float:
        """Índice de calor normalizado 0.0–1.0 para el punto."""
        raise NotImplementedError

    @abstractmethod
    async def get_fire_risk(self, lat: float, lon: float) -> float:
        """Riesgo de incendio forestal 0.0–1.0."""
        raise NotImplementedError

    @abstractmethod
    async def get_flood_risk(self, lat: float, lon: float) -> float:
        """Riesgo de inundación 0.0–1.0 (FLI Copernicus + PATRICOVA CV)."""
        raise NotImplementedError

    @abstractmethod
    async def get_climate_risk(self, lat: float, lon: float) -> ClimateRisk:
        """Snapshot climático completo para el punto."""
        raise NotImplementedError
