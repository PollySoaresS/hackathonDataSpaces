"""
Endpoints GIS — ALBA data_IA
/api/gis/catalog       → catálogo WMS + WMTS ICV
/api/gis/wfs/features  → consulta WFS vectorial (datos analíticos)
/api/gis/wms/proxy     → proxy WMS para evitar CORS desde frontend
"""
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
import httpx
from core.config import get_settings
from app.use_cases.gis_use_case import GisUseCase

router = APIRouter()
use_case = GisUseCase()
_settings = get_settings()


@router.get(
    "/catalog",
    summary="Catálogo ICV — capas WMS y WMTS disponibles",
    response_description="Listas de capas WMS y WMTS del Institut Cartogràfic Valencià",
)
async def catalog():
    """
    Devuelve las capas publicadas por el ICV.
    Si ICV_WMS_URL / ICV_WMTS_URL no están configurados, las listas son vacías
    pero el endpoint sigue respondiendo correctamente (modo sin cartografía).
    """
    return await use_case.get_catalog()


@router.get(
    "/wfs/features",
    summary="Consulta WFS ICV — datos vectoriales analíticos",
    response_description="GeoJSON FeatureCollection",
)
async def wfs_features(
    type_name: str = Query(
        ...,
        description="Nombre de capa WFS, p.e. 'ICV:municipios_cv'",
        example="ICV:municipios_cv",
    ),
    bbox: str | None = Query(
        default=None,
        description="Bounding box: minx,miny,maxx,maxy (coordenadas en srs_name)",
        example="-0.40,39.42,-0.33,39.52",
    ),
    max_features: int = Query(default=200, ge=1, le=5000),
    srs_name: str = Query(default="EPSG:4326"),
):
    """
    Consulta WFS vectorial sobre capas ICV.
    Usar preferentemente sobre WMS cuando se necesiten datos para análisis,
    rutas, ODS o contexto para la IA.
    """
    return await use_case.get_wfs_features(type_name, bbox, max_features, srs_name)


# Parámetros WMS permitidos en el proxy (whitelist SSRF)
_WMS_ALLOWED_PARAMS = {
    "SERVICE", "VERSION", "REQUEST", "LAYERS", "STYLES", "CRS", "SRS",
    "BBOX", "WIDTH", "HEIGHT", "FORMAT", "TRANSPARENT", "BGCOLOR",
    "EXCEPTIONS", "TIME", "ELEVATION", "language",
}


@router.get(
    "/wms/proxy",
    summary="Proxy WMS ICV — teselas para visualización",
    response_description="Imagen de tesela WMS",
    include_in_schema=True,
)


async def wms_proxy(request: Request):
    """
    Reenvía peticiones GetMap/GetCapabilities al ICV evitando CORS.
    Usar SOLO para visualización, no para datos analíticos.
    Solo se reenvían parámetros WMS estándar (whitelist) para prevenir SSRF.
    """
    if not _settings.ICV_WMS_URL:
        raise HTTPException(
            status_code=400,
            detail="ICV_WMS_URL no configurado. Añade la variable de entorno.",
        )
    # Filtrar únicamente parámetros WMS estándar
    raw = dict(request.query_params)
    params = {k.upper(): v for k, v in raw.items() if k.upper() in _WMS_ALLOWED_PARAMS}
    params.setdefault("SERVICE", "WMS")
    try:
        async with httpx.AsyncClient(timeout=_settings.GIS_TIMEOUT_SECONDS) as c:
            resp = await c.get(_settings.ICV_WMS_URL, params=params)
            resp.raise_for_status()
            return Response(
                content=resp.content,
                media_type=resp.headers.get("content-type", "image/png"),
                headers={"Cache-Control": "public, max-age=300"},
            )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Error al contactar ICV: {e}")
