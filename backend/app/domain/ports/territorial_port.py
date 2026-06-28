"""
Puerto Territorial — ALBA data_IA
Contrato hexagonal para contexto territorial de la Comunitat Valenciana.
Desacopla casos de uso de ICV / WFS / httpx.
"""
from abc import ABC, abstractmethod

from app.domain.entities.territorial_context import TerritorialContext


class TerritorialPort(ABC):

    @abstractmethod
    async def get_territorial_context(self, lat: float, lon: float) -> TerritorialContext:
        """Contexto territorial completo para un punto (lat, lon)."""
        raise NotImplementedError

    @abstractmethod
    async def get_municipality(self, lat: float, lon: float) -> str:
        """Nombre del municipio que contiene el punto."""
        raise NotImplementedError

    @abstractmethod
    async def get_comarca(self, lat: float, lon: float) -> str:
        """Nombre de la comarca que contiene el punto."""
        raise NotImplementedError

    @abstractmethod
    async def get_land_use(self, lat: float, lon: float) -> str:
        """Clasificación de uso del suelo: urbano|agricola|forestal|industrial|sin_datos."""
        raise NotImplementedError

    @abstractmethod
    async def is_protected_area(self, lat: float, lon: float) -> tuple[bool, list[str]]:
        """True si el punto está en una zona protegida. Devuelve (bool, [restricciones])."""
        raise NotImplementedError
