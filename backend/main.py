"""
ALBA data_IA — Backend FastAPI
Optimizador de rutas urbanas + anonimización PHI
Stack: FastAPI · Groq llama-3.1-8b-instant · Salamandra-7B (ALIA/HuggingFace)
"""

import os
from fastapi import FastAPI, HTTPException, Request, Response
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

# ── Entorno ────────────────────────────────────────────────────────────────────
_ENV = os.getenv("ENVIRONMENT", "development").lower()
_IS_PROD = _ENV == "production"

# ── Orígenes CORS (env var en producción, fallback a localhost en dev) ─────────
_allowed_origins_raw = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5175,http://127.0.0.1:5175,http://localhost:3000"
)
_ALLOWED_ORIGINS = [o.strip() for o in _allowed_origins_raw.split(",") if o.strip()]

app = FastAPI(
    title="ALBA data_IA",
    description="Middleware de optimización de rutas urbanas con anonimización PHI soberana",
    version="1.0.0",
    # En producción se ocultan docs para no exponer el esquema público
    docs_url=None if _IS_PROD else "/api/docs",
    redoc_url=None if _IS_PROD else "/api/redoc",
    openapi_url=None if _IS_PROD else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,          # Sin cookies/sesiones
    allow_methods=["GET", "POST"],     # Sólo métodos usados en la API
    allow_headers=["Content-Type"],   # Mínimo necesario
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Añade cabeceras de seguridad OWASP a todas las respuestas."""
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if _IS_PROD:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

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
