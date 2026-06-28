"""
Adaptador ICV Territorial — ALBA data_IA
Implementa TerritorialPort usando WFS 2.0.0 del ICV (Institut Cartogràfic Valencià).
Endpoint: http://terramapas.icv.gva.es/0105_Delimitaciones

Fuentes usadas:
  - ms:ICV.Municipios   → municipio + provincia
  - ms:ICV.Comarcas     → comarca

Uso del suelo y zonas protegidas: tabla estática CV mientras ICV no
expone capa de usos en el endpoint público.
"""
from __future__ import annotations

import logging

import httpx
from core.config import get_settings
from app.domain.ports.territorial_port import TerritorialPort
from app.domain.entities.territorial_context import TerritorialContext

logger = logging.getLogger("alba.territorial")

# ── Tabla estática de zonas protegidas relevantes CV ─────────────────────────
# Municipios total o parcialmente dentro de espacios naturales protegidos (ENP).
# Fuente: GVA Conselleria de Medi Ambient.
_PROTECTED_MUNICIPALITIES: dict[str, list[str]] = {
    "sueca": ["Parque Natural L'Albufera", "ZEPA", "ZEC"],
    "cullera": ["Parque Natural L'Albufera", "ZEC"],
    "gandia": ["Parque Natural Serpis", "ZEC"],
    "xàtiva": ["ZEC Serres de Martés"],
    "requena": ["Parque Natural Hoces del Cabriel", "ZEPA"],
    "benaguasil": ["ZEC Sierra Calderona"],
    "llíria": ["Parque Natural Sierra Calderona", "ZEPA", "ZEC"],
    "segorbe": ["Parque Natural Sierra Calderona", "ZEC"],
    "morella": ["ZEC Ports de Morella", "ZEPA"],
    "penyagolosa": ["Parque Natural Penyagolosa", "ZEPA", "ZEC"],
    "xodos": ["Parque Natural Penyagolosa", "ZEC"],
    "alcoi": ["Parque Natural Font Roja", "ZEC"],
    "benifallim": ["Parque Natural Font Roja", "ZEC"],
    "guardamar del segura": ["ZEC Cap Roig", "ZEPA"],
    "calp": ["ZEC Cap Prim", "ZEPA"],
    "dénia": ["Parque Natural Montgó", "ZEC", "ZEPA"],
    "jávea": ["Parque Natural Montgó", "ZEC"],
    "altea": ["ZEC Serra Gelada", "ZEPA"],
    "benidorm": ["ZEC Serra Gelada", "ZEPA"],
    "orihuela": ["Parque Natural El Hondo", "ZEPA"],
    "elx": ["Parque Natural El Hondo", "Palmeral", "ZEPA"],
    "santa pola": ["Parque Natural Salinas de Santa Pola", "ZEC", "ZEPA"],
}

# ── Clasificación de uso del suelo por tamaño municipal (simplificado) ───────
# Fuente: datos INE + SIOSE CV. En producción → reemplazar por WFS SIOSE/CORINE.
def _estimate_land_use(municipio: str, pop_hint: int = 0) -> str:
    """Estimación de uso de suelo basada en el nombre del municipio."""
    urban_large = {
        "valència", "alacant", "castelló de la plana", "elx",
        "torrent", "gandia", "orihuela", "benidorm", "alcoi",
        "vila-real", "sagunt", "dénia",
    }
    name_lower = municipio.lower()
    if name_lower in urban_large:
        return "urbano"
    protected = {k for k in _PROTECTED_MUNICIPALITIES}
    if name_lower in protected:
        return "forestal"
    return "urbano"  # default conservador para entornos urbanos


class IcvTerritorialAdapter(TerritorialPort):
    """Adaptador concreto ICV para contexto territorial."""

    def __init__(self) -> None:
        self._settings = get_settings()

    # ── Método principal ──────────────────────────────────────────────────────
    async def get_territorial_context(self, lat: float, lon: float) -> TerritorialContext:
        municipio, provincia = await self._query_municipio(lat, lon)
        comarca = await self._query_comarca(lat, lon)
        land_use = await self.get_land_use(lat, lon)
        is_protected, restricciones = await self.is_protected_area(lat, lon)

        return TerritorialContext(
            municipio=municipio,
            comarca=comarca,
            provincia=provincia,
            uso_suelo=land_use,
            zona_protegida=is_protected,
            restricciones=restricciones,
            lat=lat,
            lon=lon,
        )

    async def get_municipality(self, lat: float, lon: float) -> str:
        name, _ = await self._query_municipio(lat, lon)
        return name

    async def get_comarca(self, lat: float, lon: float) -> str:
        return await self._query_comarca(lat, lon)

    async def get_land_use(self, lat: float, lon: float) -> str:
        municipio, _ = await self._query_municipio(lat, lon)
        return _estimate_land_use(municipio)

    async def is_protected_area(self, lat: float, lon: float) -> tuple[bool, list[str]]:
        municipio, _ = await self._query_municipio(lat, lon)
        key = municipio.lower()
        restricciones = _PROTECTED_MUNICIPALITIES.get(key, [])
        return bool(restricciones), restricciones

    # ── Consultas WFS ─────────────────────────────────────────────────────────
    async def _query_wfs(
        self,
        type_name: str,
        lat: float,
        lon: float,
        buf: float = 0.005,  # ~500 m buffer
    ) -> list[dict]:
        """Consulta WFS GetFeature con BBOX alrededor del punto."""
        url = self._settings.ICV_WFS_URL
        if not url:
            return []

        bbox = f"{lon - buf},{lat - buf},{lon + buf},{lat + buf},EPSG:4326"
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": type_name,
            "outputFormat": "application/json",
            "BBOX": bbox,
            "count": "1",
        }
        try:
            async with httpx.AsyncClient(timeout=self._settings.GIS_TIMEOUT_SECONDS) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                return data.get("features", [])
        except Exception as exc:
            logger.warning("WFS %s error en (%.4f,%.4f): %s", type_name, lat, lon, exc)
            return []

    async def _query_municipio(self, lat: float, lon: float) -> tuple[str, str]:
        """Devuelve (nombre_municipio, provincia)."""
        features = await self._query_wfs("ms:ICV.Municipios", lat, lon)
        if not features:
            return self._fallback_municipio(lat, lon)

        props = features[0].get("properties", {})
        # ICV puede usar distintos nombres de campo según versión
        municipio = (
            props.get("Nmun")
            or props.get("MUNICIPIO")
            or props.get("nombre")
            or props.get("NOM_MUNI")
            or "sin_datos"
        )
        provincia = (
            props.get("Npro")
            or props.get("PROVINCIA")
            or props.get("NOM_PROV")
            or self._guess_provincia(lat, lon)
        )
        return str(municipio), str(provincia)

    async def _query_comarca(self, lat: float, lon: float) -> str:
        """Devuelve nombre de la comarca."""
        features = await self._query_wfs("ms:ICV.Comarcas", lat, lon)
        if not features:
            return self._fallback_comarca(lat, lon)

        props = features[0].get("properties", {})
        comarca = (
            props.get("Ncomar")
            or props.get("COMARCA")
            or props.get("NOM_COM")
            or props.get("nombre")
            or "sin_datos"
        )
        return str(comarca)

    # ── Fallbacks geográficos para la CV ─────────────────────────────────────
    @staticmethod
    def _guess_provincia(lat: float, lon: float) -> str:
        """Asignación de provincia por coordenadas (bounding boxes aproximados CV)."""
        if lat > 39.7:
            return "Castelló"
        if lat > 38.5:
            return "València"
        return "Alacant"

    @staticmethod
    def _fallback_municipio(lat: float, lon: float) -> tuple[str, str]:
        """Municipios de referencia cuando WFS no responde."""
        if 39.4 <= lat <= 39.6 and -0.5 <= lon <= -0.2:
            return "València", "València"
        if 38.3 <= lat <= 38.4 and -0.55 <= lon <= -0.42:
            return "Alacant", "Alacant"
        if 39.9 <= lat <= 40.1 and -0.15 <= lon <= 0.1:
            return "Castelló de la Plana", "Castelló"
        return "sin_datos", IcvTerritorialAdapter._guess_provincia(lat, lon)

    @staticmethod
    def _fallback_comarca(lat: float, lon: float) -> str:
        if 39.4 <= lat <= 39.6 and -0.5 <= lon <= -0.2:
            return "L'Horta"
        if 38.3 <= lat <= 38.4 and -0.55 <= lon <= -0.42:
            return "L'Alacantí"
        if 39.9 <= lat <= 40.1 and -0.15 <= lon <= 0.1:
            return "La Plana Alta"
        return "sin_datos"
