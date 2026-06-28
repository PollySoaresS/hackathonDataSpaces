"""
ALBA data_IA — Backend FastAPI
Optimizador de rutas urbanas + anonimización PHI
Stack: FastAPI · Groq llama3-8b-8192 · Salamandra-7B (ALIA/HuggingFace)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging

from routes.optimize import router as optimize_router
from routes.anonymize import router as anonymize_router
from routes.metrics import router as metrics_router
from routes.gis import router as gis_router
from routes.territorial import router as territorial_router
from routes.weather import router as weather_router
from routes.climate import router as climate_router
from routes.risk import router as risk_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("alba")

app = FastAPI(
    title="ALBA data_IA",
    description="Middleware de optimización de rutas urbanas con anonimización PHI soberana",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,          # Sin cookies/sesiones: no se necesita
    allow_methods=["GET", "POST"],     # Sólo métodos usados en la API
    allow_headers=["Content-Type"],   # Mínimo necesario
)

app.include_router(optimize_router,    prefix="/api/optimize",    tags=["Route Optimizer"])
app.include_router(anonymize_router,   prefix="/api/anonymize",   tags=["PHI Anonymizer"])
app.include_router(metrics_router,     prefix="/api/metrics",     tags=["CO2 Metrics"])
app.include_router(gis_router,         prefix="/api/gis",         tags=["GIS ICV"])
app.include_router(territorial_router, prefix="/api/territorial", tags=["Territorial Engine"])
app.include_router(weather_router,     prefix="/api/weather",     tags=["Weather Engine"])
app.include_router(climate_router,     prefix="/api/climate",     tags=["Climate Engine"])
app.include_router(risk_router,        prefix="/api/risk",        tags=["DS4M Risk Engine"])

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "project": "ALBA data_IA"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
