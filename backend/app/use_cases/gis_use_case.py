"""
Caso de uso GIS — ALBA data_IA
Orquesta acceso a cartografía ICV como contexto territorial
para optimización de rutas, evaluación ODS y análisis geográfico.
"""
from app.services.gis_service import GisService


class GisUseCase:
    def __init__(self, service: GisService | None = None):
        self.service = service or GisService()

    async def get_catalog(self) -> dict:
        """Catálogo de capas disponibles en ICV (WMS + WMTS)."""
        return await self.service.catalog()

    async def get_wfs_features(
        self,
        type_name: str,
        bbox: str | None = None,
        max_features: int = 200,
        srs_name: str = "EPSG:4326",
    ) -> dict:
        """
        Consulta WFS para datos vectoriales analíticos.
        Priorizado sobre WMS cuando se necesitan datos para:
          - enriquecer paradas de ruta con contexto territorial
          - evaluar ODS por zona administrativa
          - alimentar explicaciones de IA
        """
        return await self.service.wfs_features(type_name, bbox, max_features, srs_name)

    async def get_wms_proxy_url(self) -> str:
        return await self.service.wms_proxy_url()
