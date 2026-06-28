import hashlib
import hmac
import re
from core.config import get_settings

settings = get_settings()


def hmac_mask(value: str, entity_type: str, device_id: str = "alba-demo") -> str:
    """
    Enmascara un valor PHI con HMAC-SHA256 determinista.
    Salt fijo (HMAC_SALT) + device_id → mismo input produce siempre el mismo token.
    Requisito RGPD: reproductibilidad para auditorías forenses.
    """
    key = (settings.HMAC_SECRET + settings.HMAC_SALT + device_id).encode()
    digest = hmac.new(key, value.encode(), hashlib.sha256).hexdigest()[:8]
    return f"[{entity_type}_HMAC:{digest}...]"


PATTERNS = {
    "PACIENTE": re.compile(
        r"\b(?:D\.?|Dña\.?|Sr\.?|Sra\.?|Don\s+|Doña\s+)?[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+"
        r"(?:\s+(?:de\s+)?[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+){1,3}\b"
    ),
    "DIRECCIÓN": re.compile(
        r"\b(?:C/|Calle|Av\.|Avda\.|Plaza|Pza\.|Paseo|Pg\.)\s+\w+(?:\s+\w+)*,?\s*\d+"
    ),
    "MATRÍCULA": re.compile(r"\b\d{4}[A-Z]{3}\b|\b[A-Z]{1,2}\d{4}[A-Z]{3}\b"),
    "CP": re.compile(r"\b4[0-6]\d{3}\b"),
    "TELÉFONO": re.compile(r"\b(?:\+34\s?)?[6789]\d{2}[\s-]?\d{3}[\s-]?\d{3}\b"),
    "NHC": re.compile(r"\b(?:NHC|H\.C\.|Nº historia)\s*:??\s*\d{6,10}\b", re.I),
    "DNI": re.compile(r"\b\d{8}[A-Z]\b"),
}


def regex_anonymize(text: str, device_id: str = "alba-demo") -> tuple[str, list[dict]]:
    entities = []
    result = text
    for entity_type, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            original = match.group()
            masked = hmac_mask(original, entity_type, device_id)
            result = result.replace(original, masked, 1)
            entities.append({
                "original": original,
                "masked": masked,
                "type": entity_type,
                "start": match.start(),
                "end": match.end(),
            })
    return result, entities
