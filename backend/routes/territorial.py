"""
Router Territorial — ALBA data_IA
Endpoints para consulta de contexto territorial de la Comunitat Valenciana.
"""
from fastapi import APIRouter, Query, HTTPException
from app.use_cases.territorial_use_case import GetTerritorialContextUseCase

router = APIRouter()
_use_case = GetTerritorialContextUseCase()


@router.get("/context")
async def territorial_context(
    lat: float = Query(..., ge=-90, le=90, description="Latitud WGS84"),
    lon: float = Query(..., ge=-180, le=180, description="Longitud WGS84"),
):
    """
    Devuelve el contexto territorial (municipio, comarca, uso suelo, zonas protegidas)
    para un punto de la Comunitat Valenciana.
    """
    try:
        ctx = await _use_case.execute(lat, lon)
        return ctx.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/municipality")
async def get_municipality(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Municipio para un punto geográfico."""
    ctx = await _use_case.execute(lat, lon)
    return {"municipio": ctx.municipio, "provincia": ctx.provincia}


@router.get("/comarca")
async def get_comarca(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Comarca para un punto geográfico."""
    ctx = await _use_case.execute(lat, lon)
    return {"comarca": ctx.comarca}
