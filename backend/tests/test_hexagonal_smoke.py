from app.services.anonymization_service import AnonymizationService
from app.services.route_service import RouteService
import asyncio


def test_anonymization_service_uses_fallback_without_api_keys():
    service = AnonymizationService()
    result = asyncio.run(
        service.anonymize(
            "Paciente: María López, C/ Colón 14, 46004 Valencia",
            model="alia_groq_joint",
            strict_mode=True,
        )
    )
    assert result["rgpd_compliant"] is True
    assert "anonymized" in result


def test_route_service_returns_demo_metrics():
    service = RouteService()
    result = service.optimize_demo()
    assert result["scenario"] == "Valencia · El Carmen + Ruzafa + Benimaclet"
    assert "comparison" in result
