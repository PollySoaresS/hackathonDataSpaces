"""
Endpoint /api/anonymize — ALBA data_IA
Anonimización PHI con Groq + Salamandra-7B
"""

from fastapi import APIRouter, Body, Query
from pydantic import BaseModel, field_validator
from app.use_cases.anonymize_use_case import AnonymizeUseCase

router = APIRouter()
use_case = AnonymizeUseCase()

# Límites para prevenir DoS en el pipeline de IA
_MAX_TEXT_LEN = 4_000   # ~3–4 páginas de texto
_MAX_DEVICE_ID_LEN = 64
_VALID_MODELS = {"alia_groq_joint", "salamandra", "groq", "auto"}


class AnonymizeRequest(BaseModel):
    text: str
    device_id: str = "alba-demo"
    model: str = "alia_groq_joint"
    scenario: str = "demo-valencia"
    company_type: str = "operador-urbano"
    strict_mode: bool = True

    @field_validator("text")
    @classmethod
    def text_length(cls, v: str) -> str:
        if len(v) > _MAX_TEXT_LEN:
            raise ValueError(f"text excede {_MAX_TEXT_LEN} caracteres")
        return v

    @field_validator("device_id")
    @classmethod
    def device_id_safe(cls, v: str) -> str:
        if len(v) > _MAX_DEVICE_ID_LEN:
            raise ValueError("device_id demasiado largo")
        return v

    @field_validator("model")
    @classmethod
    def model_allowed(cls, v: str) -> str:
        if v not in _VALID_MODELS:
            raise ValueError(f"model debe ser uno de {_VALID_MODELS}")
        return v


@router.post("/")
async def anonymize_text(req: AnonymizeRequest = Body(...)):
    """
    Anonimiza texto con PHI (datos sanitarios / logísticos).

    Modelos disponibles:
    - groq: llama-3.1-8b-instant · sub-100ms · temperature=0.0
    - salamandra: Salamandra-7B BSC (ALIA Kit) · NER español superior
    - auto: intenta Salamandra, fallback a Groq
    """
    context_vars = {
        "scenario": req.scenario,
        "company_type": req.company_type,
        "language": "es-ES",
        "sector": "sanitario-logistico",
    }
    result = await use_case.execute(
        req.text,
        req.device_id,
        req.model,
        context_vars,
        req.strict_mode,
    )
    # RGPD: no devolver el texto original con PHI al cliente
    result.pop("original", None)
    return result


@router.get("/demo")
async def demo_anonymize(
    text: str = Query(
        default="Paciente: María López, C/ Colón 14, 46004 Valencia. Matrícula: 1234ABC",
        description="Texto con PHI a anonimizar",
    ),
    model: str = Query(default="alia_groq_joint", description="Modo de anonimización"),
):
    """Demo rápido de anonimización para el hackathon."""
    result = await use_case.execute(text, model=model)
    result.pop("original", None)
    return result
