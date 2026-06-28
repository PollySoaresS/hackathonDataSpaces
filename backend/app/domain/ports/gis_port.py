"""
Puerto GIS — ALBA data_IA
Contrato hexagonal para acceso a servicios geográficos OGC.
Desacopla casos de uso de ICV / httpx / XML.
"""
from abc import ABC, abstractmethod


class GisPort(ABC):
    @abstractmethod
    async def list_wms_layers(self) -> list[dict]:
        """Devuelve catálogo de capas WMS disponibles."""
        raise NotImplementedError

    @abstractmethod
    async def list_wmts_layers(self) -> list[dict]:
        """Devuelve catálogo de capas WMTS disponibles."""
        raise NotImplementedError

    @abstractmethod
    async def get_wfs_features(
        self,
        type_name: str,
        bbox: str | None = None,
        max_features: int = 200,
        srs_name: str = "EPSG:4326",
    ) -> dict:
        """Consulta WFS GetFeature y devuelve GeoJSON."""
        raise NotImplementedError

    @abstractmethod
    async def get_wms_proxy_url(self) -> str:
        """URL base ICV WMS para proxy."""
        raise NotImplementedError
