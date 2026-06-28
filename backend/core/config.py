"""
Configuración centralizada — ALBA data_IA
Groq API + ALIA Kit (Salamandra-7B via HuggingFace)
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
import os

# Longitud mínima aceptable para el secreto HMAC (256 bits efectivos = 32 chars)
_HMAC_MIN_LEN = 32
# Valor centinela de desarrollo — detectado explícitamente para evitar uso en prod
_HMAC_DEV_SENTINEL = "alba-dev-secret-change-in-prod"


class Settings(BaseSettings):
    # ── Groq ──────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "llama3-8b-8192"
    GROQ_TEMPERATURE: float = 0.0
    GROQ_MAX_TOKENS: int = 1024

    # ── ALIA Kit / Salamandra-7B (HuggingFace) ────────────────────────────
    HF_API_KEY: str = os.getenv("HF_API_KEY", "")
    SALAMANDRA_MODEL: str = "BSC-LT/salamandra-7b-instruct"
    HF_INFERENCE_URL: str = (
        "https://api-inference.huggingface.co/models/BSC-LT/salamandra-7b-instruct"
    )
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_URL: str = "https://api.deepseek.com/v1"

    # ── Seguridad / Criptografía ───────────────────────────────────────────
    # SIN valor por defecto fuerte: si falta en .env, arranca en modo dev con
    # advertencia. En producción debe definirse con mínimo 32 caracteres aleatorios.
    HMAC_SECRET: str = os.getenv("HMAC_SECRET", _HMAC_DEV_SENTINEL)

    @field_validator("HMAC_SECRET")
    @classmethod
    def hmac_secret_strength(cls, v: str) -> str:
        import logging
        _log = logging.getLogger("alba.config")
        if v == _HMAC_DEV_SENTINEL:
            _log.warning(
                "HMAC_SECRET usa el valor centinela de desarrollo. "
                "Define HMAC_SECRET en .env con ≥%d caracteres aleatorios antes de producción.",
                _HMAC_MIN_LEN,
            )
        elif len(v) < _HMAC_MIN_LEN:
            raise ValueError(
                f"HMAC_SECRET demasiado corto ({len(v)} chars). Mínimo {_HMAC_MIN_LEN}."
            )
        return v

    # ── CO₂ Factors (EU Regulation 2019/1242) ─────────────────────────────
    CO2_DIESEL_G_KM: float = 154.0
    CO2_HYBRID_G_KM: float = 46.0
    CO2_EV_G_KM: float = 0.0

    # ── AEMET OpenData ─────────────────────────────────────────────────────
    # Clave en: https://opendata.aemet.es/centrodedescargas/altaUsuario
    AEMET_API_KEY: str = os.getenv("AEMET_API_KEY", "")

    # ── DS4M Risk Engine — pesos (deben sumar 1.0) ─────────────────────────
    # Contexto mediterráneo CV: calor > inundación > incendio > CO2
    RISK_WEIGHT_HEAT:  float = float(os.getenv("RISK_WEIGHT_HEAT",  "0.40"))
    RISK_WEIGHT_FLOOD: float = float(os.getenv("RISK_WEIGHT_FLOOD", "0.30"))
    RISK_WEIGHT_FIRE:  float = float(os.getenv("RISK_WEIGHT_FIRE",  "0.20"))
    RISK_WEIGHT_CO2:   float = float(os.getenv("RISK_WEIGHT_CO2",   "0.10"))

    # ── GIS ICV (Institut Cartogràfic Valencià) ────────────────────────────
    ICV_WMS_URL: str = os.getenv("ICV_WMS_URL", "")
    ICV_WMTS_URL: str = os.getenv("ICV_WMTS_URL", "")
    ICV_WFS_URL: str = os.getenv("ICV_WFS_URL", "")
    GIS_TIMEOUT_SECONDS: float = float(os.getenv("GIS_TIMEOUT_SECONDS", "15"))

    # ── Valencia Demo Data ─────────────────────────────────────────────────
    DEMO_TOTAL_KM_BEFORE: float = 103.0
    DEMO_TOTAL_KM_AFTER: float = 66.0

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
