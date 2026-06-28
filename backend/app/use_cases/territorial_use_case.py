"""
Caso de uso: GetTerritorialContextUseCase — ALBA data_IA
Obtiene el contexto territorial para un punto geográfico (lat, lon).
"""
from app.services.territorial_service import TerritorialService
from app.domain.entities.territorial_context import TerritorialContext


class GetTerritorialContextUseCase:
    def __init__(self, service: TerritorialService | None = None) -> None:
        self.service = service or TerritorialService()

    async def execute(self, lat: float, lon: float) -> TerritorialContext:
        """Punto de entrada único. Valida coordenadas y devuelve contexto."""
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError(f"Coordenadas inválidas: lat={lat}, lon={lon}")
        # Bounding box aproximado de la Comunitat Valenciana
        # Se acepta cualquier punto; la búsqueda WFS retorna sin_datos fuera del dominio
        return await self.service.get_context(lat, lon)
