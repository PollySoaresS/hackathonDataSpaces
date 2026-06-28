from abc import ABC, abstractmethod


class AnonymizationPort(ABC):
    @abstractmethod
    async def anonymize(
        self,
        text: str,
        device_id: str = "alba-demo",
        model: str = "alia_groq_joint",
        context_vars: dict | None = None,
        strict_mode: bool = True,
    ) -> dict:
        raise NotImplementedError
