"""Servicio Climático — ALBA data_IA"""
from app.domain.ports.climate_port import ClimatePort
from app.infrastructure.adapters.copernicus_adapter import CopernicusAdapter
from app.domain.entities.climate_risk import ClimateRisk


class ClimateService:
    def __init__(self, port: ClimatePort | None = None) -> None:
        self.port: ClimatePort = port or CopernicusAdapter()

    async def get_risk(self, lat: float, lon: float) -> ClimateRisk:
        return await self.port.get_climate_risk(lat, lon)

    async def get_heat_index(self, lat: float, lon: float) -> float:
        return await self.port.get_heat_index(lat, lon)

    async def get_fire_risk(self, lat: float, lon: float) -> float:
        return await self.port.get_fire_risk(lat, lon)

    async def get_flood_risk(self, lat: float, lon: float) -> float:
        return await self.port.get_flood_risk(lat, lon)
