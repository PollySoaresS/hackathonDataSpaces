"""
Servicio Territorial — ALBA data_IA
Capa de aplicación que orquesta el TerritorialPort.
"""
from app.domain.ports.territorial_port import TerritorialPort
from app.infrastructure.adapters.icv_territorial_adapter import IcvTerritorialAdapter
from app.domain.entities.territorial_context import TerritorialContext


class TerritorialService:
    def __init__(self, port: TerritorialPort | None = None) -> None:
        self.port: TerritorialPort = port or IcvTerritorialAdapter()

    async def get_context(self, lat: float, lon: float) -> TerritorialContext:
        return await self.port.get_territorial_context(lat, lon)
