"""Router Climático — ALBA data_IA"""
from fastapi import APIRouter, Query, HTTPException
from app.use_cases.climate_use_case import GetClimateRiskUseCase

router = APIRouter()
_use_case = GetClimateRiskUseCase()


@router.get("/risk")
async def climate_risk(
    lat: float = Query(..., ge=-90, le=90, description="Latitud WGS84"),
    lon: float = Query(..., ge=-180, le=180, description="Longitud WGS84"),
):
    """
    Indicadores climáticos territoriales (Copernicus ERA5-Land + EFFIS + PATRICOVA).
    Datos del último ETL nocturno. No son datos en tiempo real.
    """
    try:
        risk = await _use_case.execute(lat, lon)
        return risk.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/heat")
async def heat_index(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Índice de calor superficial normalizado 0.0–1.0."""
    risk = await _use_case.execute(lat, lon)
    return {"heat_index": risk.heat_index, "lat": lat, "lon": lon}


@router.get("/fire")
async def fire_risk(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Riesgo de incendio forestal 0.0–1.0 (EFFIS)."""
    risk = await _use_case.execute(lat, lon)
    return {"fire_risk": risk.fire_risk, "lat": lat, "lon": lon}


@router.get("/flood")
async def flood_risk(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Riesgo de inundación 0.0–1.0 (PATRICOVA + Copernicus FLI)."""
    risk = await _use_case.execute(lat, lon)
    return {"flood_risk": risk.flood_risk, "lat": lat, "lon": lon}
