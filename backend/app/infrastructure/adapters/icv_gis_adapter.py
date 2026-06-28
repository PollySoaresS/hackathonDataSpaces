"""
Adaptador ICV GIS — ALBA data_IA
Infraestructura: Institut Cartogràfic Valencià (ICV)
Servicios: WMS 1.3.0 · WMTS 1.0.0 · WFS 2.0.0
"""
import logging
import xml.etree.ElementTree as ET

import httpx
from core.config import get_settings
from app.domain.ports.gis_port import GisPort

logger = logging.getLogger("alba.gis")

# Namespaces OGC
_NS_WMS = {"wms": "http://www.opengis.net/wms"}
_NS_WMTS = {
    "wmts": "http://www.opengis.net/wmts/1.0",
    "ows": "http://www.opengis.net/ows/1.1",
}


class IcvGisAdapter(GisPort):
    def __init__(self):
        self._settings = get_settings()

    # ── WMS ───────────────────────────────────────────────────────────────
    async def list_wms_layers(self) -> list[dict]:
        url = self._settings.ICV_WMS_URL
        if not url:
            logger.info("ICV_WMS_URL no configurado — catálogo WMS vacío")
            return []
        params = {"SERVICE": "WMS", "REQUEST": "GetCapabilities", "VERSION": "1.3.0"}
        try:
            async with httpx.AsyncClient(timeout=self._settings.GIS_TIMEOUT_SECONDS) as c:
                resp = await c.get(url, params=params)
                resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"WMS GetCapabilities error: {e}")
            return []
        return self._parse_wms_capabilities(resp.text)

    def _parse_wms_capabilities(self, xml_text: str) -> list[dict]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"WMS XML ParseError: {e}")
            return []
        layers: list[dict] = []
        # Capas hijas (Layer > Layer) incluyendo variantes de namespace
        for layer in root.iter():
            if not layer.tag.endswith("}Layer") and layer.tag != "Layer":
                continue
            name_el = layer.find("wms:Name", _NS_WMS)
            if name_el is None:
                name_el = layer.find("Name")
            title_el = layer.find("wms:Title", _NS_WMS)
            if title_el is None:
                title_el = layer.find("Title")
            name = name_el.text if name_el is not None else ""
            title = title_el.text if title_el is not None else name
            if name:
                layers.append({"name": name, "title": title or name, "service": "WMS"})
        return layers

    # ── WMTS ──────────────────────────────────────────────────────────────
    async def list_wmts_layers(self) -> list[dict]:
        url = self._settings.ICV_WMTS_URL
        if not url:
            logger.info("ICV_WMTS_URL no configurado — catálogo WMTS vacío")
            return []
        params = {"SERVICE": "WMTS", "REQUEST": "GetCapabilities", "VERSION": "1.0.0"}
        try:
            async with httpx.AsyncClient(timeout=self._settings.GIS_TIMEOUT_SECONDS) as c:
                resp = await c.get(url, params=params)
                resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"WMTS GetCapabilities error: {e}")
            return []
        return self._parse_wmts_capabilities(resp.text)

    def _parse_wmts_capabilities(self, xml_text: str) -> list[dict]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"WMTS XML ParseError: {e}")
            return []
        layers: list[dict] = []
        for layer in root.iter():
            if not layer.tag.endswith("}Layer") and layer.tag != "Layer":
                continue
            id_el = layer.find("ows:Identifier", _NS_WMTS)
            if id_el is None:
                id_el = layer.find("Identifier")
            title_el = layer.find("ows:Title", _NS_WMTS)
            if title_el is None:
                title_el = layer.find("Title")
            identifier = id_el.text if id_el is not None else ""
            title = title_el.text if title_el is not None else identifier
            if identifier:
                layers.append({"name": identifier, "title": title or identifier, "service": "WMTS"})
        return layers

    # ── WFS ───────────────────────────────────────────────────────────────
    async def get_wfs_features(
        self,
        type_name: str,
        bbox: str | None = None,
        max_features: int = 200,
        srs_name: str = "EPSG:4326",
    ) -> dict:
        url = self._settings.ICV_WFS_URL
        if not url:
            logger.info("ICV_WFS_URL no configurado — WFS vacío")
            return {"type": "FeatureCollection", "features": []}
        params: dict = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": type_name,
            "outputFormat": "application/json",
            "srsName": srs_name,
            "count": max_features,
        }
        if bbox:
            params["bbox"] = bbox
        try:
            async with httpx.AsyncClient(timeout=self._settings.GIS_TIMEOUT_SECONDS) as c:
                resp = await c.get(url, params=params)
                resp.raise_for_status()
                return resp.json()
        except (httpx.HTTPError, ValueError) as e:
            logger.error(f"WFS GetFeature error para {type_name}: {e}")
            return {"type": "FeatureCollection", "features": [], "error": str(e)}

    # ── Proxy URL ─────────────────────────────────────────────────────────
    async def get_wms_proxy_url(self) -> str:
        return self._settings.ICV_WMS_URL or ""
