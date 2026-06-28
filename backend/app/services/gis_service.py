"""
Servicio de aplicación GIS — ALBA data_IA
Coordina catálogo ICV y consultas WFS para contexto territorial.
"""
from app.domain.ports.gis_port import GisPort
from app.infrastructure.adapters.icv_gis_adapter import IcvGisAdapter


class GisService:
    def __init__(self, port: GisPort | None = None):
        self.port = port or IcvGisAdapter()

    async def catalog(self) -> dict:
        """Catálogo unificado WMS + WMTS."""
        wms = await self.port.list_wms_layers()
        wmts = await self.port.list_wmts_layers()
        return {"wms_layers": wms, "wmts_layers": wmts}

    async def wfs_features(
        self,
        type_name: str,
        bbox: str | None,
        max_features: int,
        srs_name: str,
    ) -> dict:
        return await self.port.get_wfs_features(type_name, bbox, max_features, srs_name)

    async def wms_proxy_url(self) -> str:
        return await self.port.get_wms_proxy_url()
