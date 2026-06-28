"""
Tests smoke — Fases 1-4: TerritorialEngine, WeatherEngine, ClimateEngine, DS4M Risk
Los 4 engines deben funcionar sin conexión a servicios externos.
"""
import pytest

# ── Fase 1: TerritorialEngine ─────────────────────────────────────────────────
def test_territorial_context_valencia():
    """Contexto territorial de Valencia ciudad (fallback WFS offline)."""
    from app.infrastructure.adapters.icv_territorial_adapter import IcvTerritorialAdapter
    adapter = IcvTerritorialAdapter()

    # Fallback síncrono para smoke test
    municipio, provincia = adapter._fallback_municipio(39.47, -0.37)
    comarca = adapter._fallback_comarca(39.47, -0.37)

    assert municipio == "València"
    assert provincia == "València"
    assert comarca == "L'Horta"


def test_territorial_protected_area():
    """Sueca debe identificarse como zona protegida (L'Albufera)."""
    from app.infrastructure.adapters.icv_territorial_adapter import _PROTECTED_MUNICIPALITIES
    assert "sueca" in _PROTECTED_MUNICIPALITIES
    restricciones = _PROTECTED_MUNICIPALITIES["sueca"]
    assert any("Albufera" in r for r in restricciones)


def test_territorial_land_use_estimate():
    """Valencia ciudad debe clasificarse como urbano."""
    from app.infrastructure.adapters.icv_territorial_adapter import _estimate_land_use
    assert _estimate_land_use("valència") == "urbano"
    assert _estimate_land_use("llíria") == "forestal"


# ── Fase 2: WeatherEngine ─────────────────────────────────────────────────────
def test_weather_risk_heat_thresholds():
    """Algoritmo de calor determinista: umbrales exactos."""
    from app.infrastructure.adapters.aemet_adapter import (
        _compute_heat_risk,
        _compute_wind_risk,
        _compute_storm_risk,
    )
    assert _compute_heat_risk(40.0) == 1.0
    assert _compute_heat_risk(36.0) == 0.8
    assert _compute_heat_risk(32.0) == 0.55
    assert _compute_heat_risk(20.0) == 0.0
    assert _compute_wind_risk(100.0) == 1.0
    assert _compute_wind_risk(10.0) == 0.0
    assert _compute_storm_risk(30.0, 50.0) == 1.0
    assert _compute_storm_risk(0.0, 0.0) == 0.0


def test_weather_neutral_fallback():
    """Sin API key debe devolver observación neutra con risk_level=low."""
    from app.infrastructure.adapters.aemet_adapter import _neutral_observation, _build_risk
    obs = _neutral_observation(39.47, -0.37)
    risk = _build_risk(obs)
    assert risk.risk_level == "low"
    assert 0.0 <= risk.risk_score <= 1.0


# ── Fase 3: ClimateEngine ─────────────────────────────────────────────────────
def test_climate_idw_valencia():
    """IDW Copernicus debe devolver índices razonables para Valencia."""
    from app.infrastructure.adapters.copernicus_adapter import _static_lookup
    heat, fire, flood, drought = _static_lookup(39.47, -0.38)  # Valencia ciudad
    assert 0.5 <= heat <= 1.0,   f"heat fuera de rango: {heat}"
    assert 0.0 <= fire <= 0.5,   f"fire inesperadamente alto para ciudad: {fire}"
    assert 0.0 <= flood <= 1.0
    assert 0.0 <= drought <= 1.0


def test_climate_idw_alta_incendio():
    """Sierra Calderona debe tener fire_risk alto (>0.7)."""
    from app.infrastructure.adapters.copernicus_adapter import _static_lookup
    _, fire, _, _ = _static_lookup(39.72, -0.55)
    assert fire >= 0.70, f"fire_risk esperado alto en Sierra Calderona: {fire}"


def test_climate_level_classification():
    """Clasificador de nivel climático compuesto."""
    from app.infrastructure.adapters.copernicus_adapter import _classify_level
    assert _classify_level(0.9, 0.9, 0.9, 0.9) == "very_high"
    assert _classify_level(0.0, 0.0, 0.0, 0.0) == "very_low"
    assert _classify_level(0.5, 0.5, 0.5, 0.5) == "medium"


# ── Fase 4: DS4M RiskEngine ───────────────────────────────────────────────────
def test_risk_formula_exact():
    """Verificar la fórmula ponderada exacta."""
    from app.services.risk_service import RiskService
    svc = RiskService(heat_weight=0.40, flood_weight=0.30, fire_weight=0.20, co2_weight=0.10)
    score = svc.compute_risk(heat=1.0, flood=1.0, fire=1.0, co2=1.0)
    assert score.risk_score == 1.0
    assert score.risk_level == "very_high"


def test_risk_formula_zero():
    """Riesgo cero → very_low."""
    from app.services.risk_service import RiskService
    svc = RiskService()
    score = svc.compute_risk(0.0, 0.0, 0.0, 0.0)
    assert score.risk_score == 0.0
    assert score.risk_level == "very_low"


def test_risk_formula_weighted():
    """Solo heat activo → contribución proporcional al peso."""
    from app.services.risk_service import RiskService
    svc = RiskService(heat_weight=0.40, flood_weight=0.30, fire_weight=0.20, co2_weight=0.10)
    score = svc.compute_risk(heat=1.0, flood=0.0, fire=0.0, co2=0.0)
    assert abs(score.risk_score - 0.40) < 0.001
    assert score.heat_contribution == pytest.approx(0.40, abs=0.001)
    assert score.flood_contribution == 0.0


def test_risk_clamp_out_of_range():
    """Valores fuera de [0,1] deben ser clampados."""
    from app.services.risk_service import RiskService
    svc = RiskService()
    score = svc.compute_risk(heat=2.0, flood=-1.0, fire=0.5, co2=0.0)
    assert 0.0 <= score.risk_score <= 1.0


# ── Fase 5: VRP con climate_risk ─────────────────────────────────────────────
def test_vrp_climate_risk_disabled():
    """Con climate_risk_weight=0, el resultado es idéntico al original."""
    from services.vrp_optimizer import Stop, Vehicle, clarke_wright_savings
    stops = [
        Stop("s1", "Parada A", 39.47, -0.37, demand=1.0, climate_risk=0.8),
        Stop("s2", "Parada B", 39.48, -0.36, demand=1.0, climate_risk=0.2),
    ]
    vehicles = [Vehicle("v1", "diesel", 10.0, 39.46, -0.38)]

    result_plain  = clarke_wright_savings(stops, vehicles, climate_risk_weight=0.0)
    result_risk   = clarke_wright_savings(stops, vehicles, climate_risk_weight=0.5)

    assert result_plain["climate_risk_enabled"] is False
    assert result_risk["climate_risk_enabled"] is True
    # Con riesgo activo la distancia efectiva puede cambiar, pero km reales iguales
    assert result_plain["after"]["total_km"] == result_risk["after"]["total_km"]
