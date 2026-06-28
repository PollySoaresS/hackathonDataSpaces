"""
Smoke tests GIS — ALBA data_IA
Valida que GisService y GisUseCase cumplen el contrato
sin necesitar URLs ICV reales (ICV_WMS_URL vacío → listas vacías, no errores).
"""
import asyncio
import sys
import os

# Asegurar que backend/ está en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.gis_service import GisService
from app.use_cases.gis_use_case import GisUseCase


def test_gis_service_catalog_contract():
    """Catálogo debe tener claves wms_layers y wmts_layers (aunque vacías)."""
    result = asyncio.run(GisService().catalog())
    assert "wms_layers" in result, "Falta clave wms_layers"
    assert "wmts_layers" in result, "Falta clave wmts_layers"
    assert isinstance(result["wms_layers"], list)
    assert isinstance(result["wmts_layers"], list)


def test_gis_use_case_wfs_empty_url():
    """Sin ICV_WFS_URL configurado, WFS devuelve FeatureCollection vacía."""
    os.environ.pop("ICV_WFS_URL", None)
    result = asyncio.run(
        GisUseCase().get_wfs_features(
            type_name="ICV:test",
            bbox=None,
            max_features=10,
            srs_name="EPSG:4326",
        )
    )
    assert result["type"] == "FeatureCollection"
    assert isinstance(result["features"], list)
