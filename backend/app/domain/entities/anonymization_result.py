from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AnonymizationResult:
    original: str
    anonymized: str
    entities: list[dict[str, Any]]
    model_used: str
    temperature: float | None
    method: str
    rgpd_compliant: bool
    note: str | None = None
