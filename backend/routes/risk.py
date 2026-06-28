"""Router DS4M Risk — ALBA data_IA"""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from app.use_cases.risk_use_case import ComputeRiskUseCase

router = APIRouter()
_use_case = ComputeRiskUseCase()


class RiskDirectInput(BaseModel):
    heat: float  = Field(..., ge=0.0, le=1.0, description="Índice calor 0.0–1.0")
    flood: float = Field(..., ge=0.0, le=1.0, description="Índice inundación 0.0–1.0")
    fire: float  = Field(..., ge=0.0, le=1.0, description="Índice incendio 0.0–1.0")
    co2: float   = Field(0.0, ge=0.0, le=1.0, description="Índice CO2 0.0–1.0")


@router.post("/compute")
def compute_risk_direct(body: RiskDirectInput):
    """
    Motor DS4M: calcula riesgo compuesto a partir de índices ya normalizados.
    Síncrono. Sin red. Determinista.
    Formula: risk = w_heat*heat + w_flood*flood + w_fire*fire + w_co2*co2
    """
    score = _use_case.compute_direct(
        heat=body.heat,
        flood=body.flood,
        fire=body.fire,
        co2=body.co2,
    )
    return score.to_dict()


@router.get("/location")
async def compute_risk_location(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    co2_index: float = Query(0.0, ge=0.0, le=1.0, description="Proporción emisiones vs baseline"),
):
    """
    Riesgo compuesto DS4M para una coordenada.
    Integra automáticamente ClimateEngine (Copernicus) + WeatherEngine (AEMET).
    """
    try:
        score = await _use_case.compute_for_location(lat, lon, co2_index)
        return score.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
