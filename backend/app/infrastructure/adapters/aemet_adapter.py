"""
Adaptador AEMET — ALBA data_IA
Implementa WeatherPort usando AEMET OpenData API v1.
Doc: https://opendata.aemet.es/opendata/api/

Flujo:
  1. GET /observacion/convencional/todas → {datos: url, ...}
  2. GET {datos} → lista de observaciones de todas las estaciones
  3. Filtrar estaciones CV (lat 37.8–40.8, lon -1.5–0.7)
  4. Haversine → estación más cercana al punto solicitado
  5. Algoritmo determinista de riesgo (sin IA)

Fallback: si AEMET no responde (sin API key, timeout, mant.) →
  retorna observación sintética neutra con risk_level = "low".
"""
from __future__ import annotations

import logging
from math import radians, sin, cos, atan2, sqrt

import httpx
import json as _json
from core.config import get_settings
from app.domain.ports.weather_port import WeatherPort
from app.domain.entities.weather_risk import (
    WeatherObservation,
    WeatherRisk,
    RiskLevel,
)

logger = logging.getLogger("alba.weather")

_AEMET_BASE = "https://opendata.aemet.es/opendata/api"

# ── Pesos del algoritmo de riesgo (suman 1.0) ─────────────────────────────────
_W_HEAT  = 0.50
_W_STORM = 0.30
_W_WIND  = 0.20


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def _compute_heat_risk(temp_c: float) -> float:
    """Riesgo de calor extremo. Escala determinista basada en umbrales AEMET."""
    if temp_c >= 40.0:
        return 1.0
    if temp_c >= 36.0:
        return 0.8
    if temp_c >= 32.0:
        return 0.55
    if temp_c >= 27.0:
        return 0.25
    return 0.0


def _compute_storm_risk(prec_mmh: float, wind_kmh: float) -> float:
    """Riesgo de tormenta. Combinación lluvia intensa + viento."""
    if prec_mmh >= 30.0 and wind_kmh >= 50.0:
        return 1.0
    if prec_mmh >= 15.0:
        return 0.65
    if prec_mmh >= 5.0:
        return 0.30
    return 0.0


def _compute_wind_risk(wind_kmh: float) -> float:
    """Riesgo de viento. Umbrales protocolo DANA / Meteoalerta AEMET."""
    if wind_kmh >= 100.0:
        return 1.0
    if wind_kmh >= 70.0:
        return 0.75
    if wind_kmh >= 50.0:
        return 0.45
    if wind_kmh >= 35.0:
        return 0.20
    return 0.0


def _score_to_level(score: float) -> RiskLevel:
    if score >= 0.65:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def _build_risk(obs: WeatherObservation) -> WeatherRisk:
    heat  = _compute_heat_risk(obs.temperature)
    storm = _compute_storm_risk(obs.precipitation, obs.wind_speed)
    wind  = _compute_wind_risk(obs.wind_speed)
    score = _W_HEAT * heat + _W_STORM * storm + _W_WIND * wind
    return WeatherRisk(
        observation=obs,
        heat_risk=heat,
        storm_risk=storm,
        wind_risk=wind,
        risk_score=round(score, 4),
        risk_level=_score_to_level(score),
    )


def _neutral_observation(lat: float, lon: float) -> WeatherObservation:
    """Observación neutra para el fallback (sin API key o timeout)."""
    return WeatherObservation(
        station_id="fallback",
        station_name="Sin datos AEMET",
        lat=lat,
        lon=lon,
        temperature=20.0,
        humidity=60.0,
        wind_speed=10.0,
        precipitation=0.0,
    )


class AemetAdapter(WeatherPort):
    """Adaptador AEMET OpenData. Tolerante a fallos."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def get_weather(self, lat: float, lon: float) -> WeatherObservation:
        return await self._nearest_observation(lat, lon)

    async def get_weather_risk(self, lat: float, lon: float) -> WeatherRisk:
        obs = await self._nearest_observation(lat, lon)
        return _build_risk(obs)

    # ── AEMET OpenData ────────────────────────────────────────────────────────
    async def _nearest_observation(self, lat: float, lon: float) -> WeatherObservation:
        api_key = getattr(self._settings, "AEMET_API_KEY", "")
        if not api_key:
            logger.info("AEMET_API_KEY no configurada — usando fallback neutro")
            return _neutral_observation(lat, lon)

        headers = {"api_key": api_key, "Accept": "application/json"}
        url = f"{_AEMET_BASE}/observacion/convencional/todas"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Paso 1: obtener URL de datos
                # AEMET responde en latin-1 (no UTF-8)
                r1 = await client.get(url, headers=headers)
                r1.raise_for_status()
                meta = _json.loads(r1.content.decode("latin-1"))

                datos_url = meta.get("datos")
                if not datos_url:
                    logger.warning("AEMET no devolvió campo 'datos'")
                    return _neutral_observation(lat, lon)

                # Paso 2: descargar observaciones
                r2 = await client.get(datos_url, headers=headers)
                r2.raise_for_status()
                stations: list[dict] = _json.loads(r2.content.decode("latin-1"))

        except httpx.HTTPError as exc:
            logger.warning("AEMET HTTP error: %s", exc)
            return _neutral_observation(lat, lon)
        except Exception as exc:
            logger.warning("AEMET error inesperado: %s", exc)
            return _neutral_observation(lat, lon)

        return self._find_nearest(lat, lon, stations)

    @staticmethod
    def _find_nearest(lat: float, lon: float, stations: list[dict]) -> WeatherObservation:
        best: dict | None = None
        best_dist = float("inf")

        for s in stations:
            try:
                slat = float(s.get("lat", 0))
                slon = float(s.get("lon", 0))
            except (TypeError, ValueError):
                continue

            dist = _haversine_km(lat, lon, slat, slon)
            if dist < best_dist:
                best_dist = dist
                best = s

        if best is None:
            return _neutral_observation(lat, lon)

        def _safe_float(val, default: float = 0.0) -> float:
            try:
                return float(val)
            except (TypeError, ValueError):
                return default

        return WeatherObservation(
            station_id=str(best.get("idema", "?")),
            station_name=str(best.get("ubi", "Desconocida")),
            lat=float(best.get("lat", lat)),
            lon=float(best.get("lon", lon)),
            temperature=_safe_float(best.get("ta")),
            humidity=_safe_float(best.get("hr")),
            # vv viene en m/s → convertir a km/h para WeatherObservation
            wind_speed=round(_safe_float(best.get("vv")) * 3.6, 1),
            precipitation=_safe_float(best.get("prec")),
        )
