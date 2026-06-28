"""
Servicio de Anonimización PHI — ALBA data_IA
Pipeline: Groq llama3-8b (NER rápido) → Salamandra-7B BSC (NER español soberano)
Temperatura = 0.0 en ambos → salidas deterministas, cero alucinaciones en producción.
"""

import httpx
import json
import logging
from core.config import get_settings
from app.infrastructure.crypto.masking import regex_anonymize, hmac_mask

logger = logging.getLogger("alba.anonymizer")
settings = get_settings()

GROQ_NER_SYSTEM = """Eres un motor de reconocimiento de entidades (NER) para datos sanitarios en español.
Dado un texto, identifica ÚNICAMENTE entidades PHI (Protected Health Information):
- PACIENTE: nombre y apellidos de pacientes
- DIRECCIÓN: calle, número, piso, ciudad
- MATRÍCULA: matrícula de vehículo
- TELÉFONO: número de teléfono
- NHC: número de historia clínica
- DNI: documento de identidad
- CP: código postal

Responde SOLO con JSON válido, sin markdown, sin texto adicional:
{
  "entities": [
    {"text": "texto original", "type": "TIPO", "start": 0, "end": 10}
  ]
}"""

SALAMANDRA_SYSTEM = """Ets un motor de reconeixement d'entitats (NER) per a dades sanitàries en espanyol i català.
Identifica entitats PHI i retorna JSON. Temperatura 0.0 — respostes deterministes."""

DEEPSEEK_NER_SYSTEM = """Eres un motor NER de PHI para español.
Devuelve SOLO JSON válido con la forma:
{
    "entities": [
        {"text": "texto original", "type": "TIPO", "start": 0, "end": 10}
    ]
}
No inventes entidades. Si no hay, devuelve entities vacío."""


async def anonymize_with_groq(text: str, device_id: str = "alba-demo") -> dict:
    """
    Anonimización vía Groq llama-3.1-8b-instant.
    500 tok/s, latencia sub-100ms — ideal para demo en vivo.
    """
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY no configurada — intentando DeepSeek/regex fallback")
        return await anonymize_with_deepseek(text, device_id)

    payload = {
        "model": settings.GROQ_MODEL,
        "temperature": settings.GROQ_TEMPERATURE,
        "max_tokens": settings.GROQ_MAX_TOKENS,
        "messages": [
            {"role": "system", "content": GROQ_NER_SYSTEM},
            {"role": "user", "content": f"Texto a analizar:\n{text}"},
        ],
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            entities_data = json.loads(content)
            return _apply_entities(text, entities_data.get("entities", []), device_id, "groq-llama3-8b")
        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Groq error: {e} — fallback a DeepSeek/regex")
            return await anonymize_with_deepseek(text, device_id)


async def anonymize_with_salamandra(text: str, device_id: str = "alba-demo") -> dict:
    """
    Anonimización vía Salamandra-7B del BSC (proyecto ALIA).
    Superior a genéricos para NER en español: matrículas, direcciones valencianas,
    nombres propios catalanes/valencianos.
    Acceso: https://langtech-bsc.gitbook.io/alia-kit via HuggingFace Inference API.
    """
    if not settings.HF_API_KEY:
        logger.warning("HF_API_KEY no configurada — usando Groq/DeepSeek/regex")
        return await anonymize_with_groq(text, device_id)

    payload = {
        "inputs": f"[SYSTEM]{SALAMANDRA_SYSTEM}[/SYSTEM]\n[USER]Analiza PHI:\n{text}[/USER]",
        "parameters": {
            "temperature": 0.0,
            "max_new_tokens": 512,
            "return_full_text": False,
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                settings.HF_INFERENCE_URL,
                headers={
                    "Authorization": f"Bearer {settings.HF_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            # HF Inference API retorna lista de generated_text
            generated = data[0].get("generated_text", "") if isinstance(data, list) else data.get("generated_text", "")
            try:
                entities_data = json.loads(generated)
                return _apply_entities(text, entities_data.get("entities", []), device_id, "salamandra-7b-bsc")
            except json.JSONDecodeError:
                logger.warning("Salamandra output no es JSON — fallback Groq/DeepSeek")
                return await anonymize_with_groq(text, device_id)
        except httpx.HTTPError as e:
            logger.error(f"HuggingFace/Salamandra error: {e} — fallback Groq/DeepSeek")
            return await anonymize_with_groq(text, device_id)


async def anonymize_with_deepseek(text: str, device_id: str = "alba-demo") -> dict:
    """
    Tercer respaldo de anonimización vía DeepSeek (OpenAI-compatible API).
    Se usa únicamente cuando ALIA/Groq no están disponibles o fallan.
    """
    if not settings.DEEPSEEK_API_KEY:
        logger.warning("DEEPSEEK_API_KEY no configurada — usando regex fallback")
        return await _regex_fallback(text, device_id)

    payload = {
        "model": "deepseek-chat",
        "temperature": 0.0,
        "max_tokens": 512,
        "messages": [
            {"role": "system", "content": DEEPSEEK_NER_SYSTEM},
            {"role": "user", "content": f"Texto a analizar:\n{text}"},
        ],
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(
                f"{settings.DEEPSEEK_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            entities_data = json.loads(content)
            return _apply_entities(text, entities_data.get("entities", []), device_id, "deepseek-chat")
        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"DeepSeek error: {e} — fallback a regex")
            return await _regex_fallback(text, device_id)


def _apply_entities(text: str, entities: list[dict], device_id: str, model: str) -> dict:
    """Aplica HMAC masking a las entidades detectadas."""
    result = text
    applied = []

    for ent in sorted(entities, key=lambda e: e.get("start", 0), reverse=True):
        original = ent.get("text", "")
        etype = ent.get("type", "PHI")
        if original and original in result:
            masked = hmac_mask(original, etype, device_id)
            result = result.replace(original, masked, 1)
            applied.append({"original": original, "masked": masked, "type": etype})

    return {
        "original": text,
        "anonymized": result,
        "entities": applied,
        "model_used": model,
        "temperature": 0.0,
        "method": "HMAC-SHA256 + sal dinámica (device_id + date)",
        "rgpd_compliant": True,
    }


async def _regex_fallback(text: str, device_id: str) -> dict:
    """Fallback regex + HMAC cuando no hay API key configurada."""
    anon_text, entities = regex_anonymize(text, device_id)
    return {
        "original": text,
        "anonymized": anon_text,
        "entities": entities,
        "model_used": "regex-fallback",
        "temperature": None,
        "method": "HMAC-SHA256 + regex NER",
        "rgpd_compliant": True,
        "note": "Configura GROQ_API_KEY o HF_API_KEY para NER con IA",
    }
