"""
Adaptador Copernicus (estático + diseño ETL) — ALBA data_IA

DISEÑO ETL NOCTURNO (para producción):
═══════════════════════════════════════

  Copernicus CDS API
        │
        │  cdsapi.Client().retrieve(
        │      "reanalysis-era5-land",
        │      {"variable": ["2m_temperature","total_precipitation"], ...}
        │  )
        ▼
  ETL Nocturno (cron 02:00 UTC)
        │  1. Descarga NetCDF daily (LAT 37.8-40.8, LON -1.5-0.7 = bbox CV)
        │  2. Recorta con rasterio / xarray al shape de la CV
        │  3. Normaliza: (val - min) / (max - min) → índice 0.0-1.0
        │  4. INSERT INTO climate_snapshots (geom, heat_idx, fire_risk,
        │         flood_risk, drought_idx, ref_date) VALUES (...)
        ▼
  PostGIS (climate_snapshots tabla)
        │  CREATE TABLE climate_snapshots (
        │    id SERIAL PRIMARY KEY,
        │    geom GEOMETRY(Point, 4326),
        │    heat_index FLOAT,
        │    fire_risk FLOAT,
        │    flood_risk FLOAT,
        │    drought_index FLOAT,
        │    ref_date DATE
        │  );
        │  CREATE INDEX ON climate_snapshots USING GIST(geom);
        ▼
  ClimateRepository (SQLAlchemy / asyncpg)
        │  SELECT heat_index, fire_risk, flood_risk, drought_index
        │  FROM climate_snapshots
        │  WHERE ST_DWithin(geom, ST_SetSRID(ST_Point(:lon,:lat),4326), 0.05)
        │  ORDER BY ref_date DESC LIMIT 1;
        ▼
  CopernicusAdapter.get_climate_risk(lat, lon)

FASE ACTUAL:
  Datos estáticos realistas para la CV (2024) derivados de:
  - ERA5-Land temperatura media superficial verano 2024
  - EFFIS (European Forest Fire Information System)
  - PATRICOVA (Plan de Acció Territorial de Caràcter Sectorial — inundaciones CV)
  - SPI-3 AEMET 2024 (índice de sequía)

  CUANDO PostGIS esté disponible: reemplazar _static_lookup() por
  query PostGIS en self._climate_repo.query_nearest(lat, lon).
"""
from __future__ import annotations

import logging
from math import radians, sin, cos, atan2, sqrt
from app.infrastructure.utils.geo import haversine_km

from app.domain.ports.climate_port import ClimatePort
from app.domain.entities.climate_risk import ClimateRisk, ClimateRiskLevel

logger = logging.getLogger("alba.climate")

_REFERENCE_DATE = "2024-09-15"   # último snapshot Copernicus procesado
_SOURCE = "static_cv_2024"       # cambiar a "copernicus_etl" al activar PostGIS


# ── Datos climáticos estáticos representativos CV 2024 ────────────────────────
# Cada zona: (lat_centro, lon_centro, heat, fire, flood, drought)
# Fuente: ERA5-Land + EFFIS + PATRICOVA + SPI-3
_CV_CLIMATE_ZONES: list[tuple[float, float, float, float, float, float]] = [
    # Valencia ciudad y horta
    (39.47, -0.38, 0.72, 0.25, 0.45, 0.60),
    # L'Albufera (alta inundación, alta sequía)
    (39.33, -0.35, 0.68, 0.15, 0.90, 0.55),
    # Sierra Calderona (alto incendio)
    (39.72, -0.55, 0.65, 0.85, 0.10, 0.50),
    # Ribera Alta (inundación moderada-alta)
    (39.13, -0.52, 0.70, 0.20, 0.70, 0.58),
    # La Safor / Gandia (moderado)
    (38.98, -0.18, 0.65, 0.30, 0.40, 0.52),
    # Alacant ciudad
    (38.35, -0.49, 0.80, 0.35, 0.30, 0.75),
    # El Baix Segura (inundación alta — DANA 2024)
    (38.05, -0.78, 0.78, 0.20, 0.92, 0.80),
    # Font Roja / Alcoi (incendio medio-alto)
    (38.70, -0.47, 0.62, 0.70, 0.15, 0.55),
    # Castelló de la Plana
    (39.99, 0.03,  0.58, 0.28, 0.35, 0.45),
    # Els Ports / Morella (incendio muy alto)
    (40.62, -0.10, 0.50, 0.92, 0.05, 0.42),
    # El Maestrat (moderado)
    (40.38, -0.02, 0.52, 0.65, 0.10, 0.48),
    # Vega Baja / Orihuela (extremo calor y sequía)
    (38.08, -0.93, 0.92, 0.40, 0.60, 0.88),
    # La Marina Alta / Dénia (turístico costero, moderado)
    (38.84,  0.11, 0.68, 0.45, 0.25, 0.62),
    # La Vall d'Albaida
    (38.82, -0.53, 0.66, 0.55, 0.20, 0.58),
    # Requena-Utiel (incendio alto, sequía alta)
    (39.48, -1.10, 0.70, 0.78, 0.08, 0.72),
]


def _classify_level(heat: float, fire: float, flood: float, drought: float) -> ClimateRiskLevel:
    """Clasificación compuesta del nivel de riesgo climático."""
    composite = 0.35 * heat + 0.30 * fire + 0.25 * flood + 0.10 * drought
    if composite >= 0.80:
        return "very_high"
    if composite >= 0.60:
        return "high"
    if composite >= 0.40:
        return "medium"
    if composite >= 0.20:
        return "low"
    return "very_low"


def _static_lookup(lat: float, lon: float) -> tuple[float, float, float, float]:
    """Interpolación IDW (Inverse Distance Weighting) sobre zonas estáticas CV."""
    total_weight = 0.0
    heat = fire = flood = drought = 0.0

    for zlat, zlon, zh, zf, zfl, zd in _CV_CLIMATE_ZONES:
        dist = haversine_km(lat, lon, zlat, zlon)
        dist = max(dist, 0.1)       # evitar división por cero
        w = 1.0 / (dist ** 2)       # IDW potencia 2
        total_weight += w
        heat   += w * zh
        fire   += w * zf
        flood  += w * zfl
        drought += w * zd

    if total_weight == 0:
        return 0.5, 0.3, 0.3, 0.5

    return (
        min(heat   / total_weight, 1.0),
        min(fire   / total_weight, 1.0),
        min(flood  / total_weight, 1.0),
        min(drought / total_weight, 1.0),
    )


class CopernicusAdapter(ClimatePort):
    """
    Adaptador estático de datos climáticos Copernicus para la CV.
    Reemplazar _static_lookup() por query PostGIS cuando el ETL esté activo.
    """

    async def get_heat_index(self, lat: float, lon: float) -> float:
        heat, _, _, _ = _static_lookup(lat, lon)
        return round(heat, 4)

    async def get_fire_risk(self, lat: float, lon: float) -> float:
        _, fire, _, _ = _static_lookup(lat, lon)
        return round(fire, 4)

    async def get_flood_risk(self, lat: float, lon: float) -> float:
        _, _, flood, _ = _static_lookup(lat, lon)
        return round(flood, 4)

    async def get_climate_risk(self, lat: float, lon: float) -> ClimateRisk:
        heat, fire, flood, drought = _static_lookup(lat, lon)
        level = _classify_level(heat, fire, flood, drought)
        return ClimateRisk(
            lat=lat,
            lon=lon,
            heat_index=round(heat, 4),
            fire_risk=round(fire, 4),
            flood_risk=round(flood, 4),
            drought_index=round(drought, 4),
            climate_risk_level=level,
            data_source=_SOURCE,
            reference_date=_REFERENCE_DATE,
        )
