from app.domain.ports.anonymization_port import AnonymizationPort
from app.infrastructure.crypto.masking import hmac_mask, regex_anonymize
from app.infrastructure.ai_clients.ner_clients import anonymize_with_deepseek, anonymize_with_groq, anonymize_with_salamandra


class AnonymizationAdapter(AnonymizationPort):
    async def anonymize(
        self,
        text: str,
        device_id: str = "alba-demo",
        model: str = "alia_groq_joint",
        context_vars: dict | None = None,
        strict_mode: bool = True,
    ) -> dict:
        vars_ctx = context_vars or {}

        if model == "groq":
            result = await anonymize_with_groq(text, device_id)
        elif model == "salamandra":
            result = await anonymize_with_salamandra(text, device_id)
        elif model in {"alia_groq_joint", "auto"}:
            salamandra_result = await anonymize_with_salamandra(text, device_id)
            groq_result = await anonymize_with_groq(text, device_id)
            result = self._merge_joint_results(text, device_id, salamandra_result, groq_result)
            if not result.get("entities"):
                deepseek_result = await anonymize_with_deepseek(text, device_id)
                if deepseek_result.get("entities"):
                    result = deepseek_result
        else:
            result = await anonymize_with_salamandra(text, device_id)

        if strict_mode and not result.get("entities"):
            fallback_text, fallback_entities = regex_anonymize(text, device_id)
            result = {
                "original": text,
                "anonymized": fallback_text,
                "entities": fallback_entities,
                "model_used": f"{result.get('model_used', 'unknown')}+regex-guardrail",
                "temperature": 0.0,
                "method": "Guardrail estricto: consenso IA + regex",
                "rgpd_compliant": True,
            }

        result["context_vars"] = {
            "language": vars_ctx.get("language", "es-ES"),
            "sector": vars_ctx.get("sector", "sanitario-logistico"),
            "company_type": vars_ctx.get("company_type", "operador urbano"),
            "scenario": vars_ctx.get("scenario", "demo-valencia"),
        }
        result["hallucination_guardrails"] = [
            "temperature=0.0",
            "solo PHI detectada",
            "enmascarado HMAC determinista",
            "fallback regex en modo estricto",
        ]
        return result

    def _merge_joint_results(self, text: str, device_id: str, salamandra_result: dict, groq_result: dict) -> dict:
        unique_entities: dict[tuple[str, str], dict] = {}
        for entity in salamandra_result.get("entities", []):
            original = entity.get("original") or entity.get("text")
            etype = entity.get("type", "PHI")
            if original:
                unique_entities[(original, etype)] = {"original": original, "type": etype}
        for entity in groq_result.get("entities", []):
            original = entity.get("original") or entity.get("text")
            etype = entity.get("type", "PHI")
            if original:
                unique_entities[(original, etype)] = {"original": original, "type": etype}

        anonymized = text
        applied: list[dict] = []
        for _, entity in sorted(unique_entities.items(), key=lambda item: len(item[0][0]), reverse=True):
            original = entity["original"]
            etype = entity["type"]
            if original in anonymized:
                masked = hmac_mask(original, etype, device_id)
                anonymized = anonymized.replace(original, masked, 1)
                applied.append({"original": original, "masked": masked, "type": etype})

        return {
            "original": text,
            "anonymized": anonymized,
            "entities": applied,
            "model_used": "alia-salamandra+groq-consensus",
            "temperature": 0.0,
            "method": "Consenso ALIA+Groq con fusión de entidades",
            "rgpd_compliant": True,
        }
