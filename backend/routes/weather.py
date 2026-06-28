"""Router Meteorológico — ALBA data_IA"""
from fastapi import APIRouter, Query, HTTPException
from app.use_cases.weather_use_case import GetWeatherRiskUseCase

router = APIRouter()
_use_case = GetWeatherRiskUseCase()


@router.get("/risk")
async def weather_risk(
    lat: float = Query(..., ge=-90, le=90, description="Latitud WGS84"),
    lon: float = Query(..., ge=-180, le=180, description="Longitud WGS84"),
):
    """
    Retorna condiciones meteorológicas actuales (estación AEMET más cercana)
    y nivel de riesgo calculado deterministamente: low | medium | high.
    """
    try:
        risk = await _use_case.execute(lat, lon)
        return risk.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/observation")
async def weather_observation(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Solo la observación, sin cálculo de riesgo."""
    risk = await _use_case.execute(lat, lon)
    return risk.observation.__dict__
