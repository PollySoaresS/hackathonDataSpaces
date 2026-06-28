from app.domain.ports.anonymization_port import AnonymizationPort
from app.infrastructure.adapters.anonymization_adapter import AnonymizationAdapter


class AnonymizationService:
    def __init__(self, port: AnonymizationPort | None = None):
        self.port = port or AnonymizationAdapter()

    async def anonymize(
        self,
        text: str,
        device_id: str = "alba-demo",
        model: str = "alia_groq_joint",
        context_vars: dict | None = None,
        strict_mode: bool = True,
    ) -> dict:
        return await self.port.anonymize(text, device_id, model, context_vars, strict_mode)
