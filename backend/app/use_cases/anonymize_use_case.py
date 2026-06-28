from app.services.anonymization_service import AnonymizationService


class AnonymizeUseCase:
    def __init__(self, service: AnonymizationService | None = None):
        self.service = service or AnonymizationService()

    async def execute(
        self,
        text: str,
        device_id: str = "alba-demo",
        model: str = "alia_groq_joint",
        context_vars: dict | None = None,
        strict_mode: bool = True,
    ) -> dict:
        return await self.service.anonymize(text, device_id, model, context_vars, strict_mode)
