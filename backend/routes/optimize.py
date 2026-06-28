"""
Endpoint /api/optimize — ALBA data_IA
Clarke-Wright Savings VRP con datos de Valencia
"""

from fastapi import APIRouter, Body
from pydantic import BaseModel
from app.use_cases.optimize_use_case import OptimizeUseCase

router = APIRouter()
use_case = OptimizeUseCase()


class OptimizeRequest(BaseModel):
    stops: list[dict] = []
    vehicles: list[dict] = []
    use_demo: bool = True


@router.post("/")
async def optimize_routes(req: OptimizeRequest = Body(...)):
    """
    Optimiza rutas usando Clarke-Wright Savings VRP.
    - use_demo=True: usa el escenario Valencia predefinido
    - use_demo=False: usa los stops y vehicles del body
    """
    return use_case.execute(req.stops, req.vehicles, req.use_demo)


@router.get("/demo")
async def demo_metrics():
    """Devuelve métricas fijas del demo de Valencia para el frontend."""
    return use_case.demo_metrics()
