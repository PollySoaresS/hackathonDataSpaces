"""
Entidad de dominio — ClimateRisk
Indicadores climáticos territoriales (Copernicus/ETL nocturno).
NO son datos en tiempo real. Son resultado del ETL diario.
"""
from dataclasses import dataclass
from typing import Literal

ClimateRiskLevel = Literal["very_low", "low", "medium", "high", "very_high"]


@dataclass(frozen=True)
class ClimateRisk:
    """
    Snapshot climático de un punto territorial.
    Fuente: PostGIS repository alimentado por ETL nocturno Copernicus CDS.
    """
    lat: float
    lon: float

    # Índices 0.0–1.0
    heat_index: float       # temperatura superficial normalizada
    fire_risk: float        # riesgo incendio forestal
    flood_risk: float       # riesgo inundación DANA/FLI
    drought_index: float    # índice sequía SPI-3

    # Clasificación del nivel global
    climate_risk_level: ClimateRiskLevel

    # Metadatos del dato
    data_source: str        # "copernicus_etl" | "static_cv_2024"
    reference_date: str     # ISO date del último ETL

    def to_dict(self) -> dict:
        return {
            "location": {"lat": self.lat, "lon": self.lon},
            "indices": {
                "heat_index": round(self.heat_index, 3),
                "fire_risk": round(self.fire_risk, 3),
                "flood_risk": round(self.flood_risk, 3),
                "drought_index": round(self.drought_index, 3),
            },
            "climate_risk_level": self.climate_risk_level,
            "metadata": {
                "data_source": self.data_source,
                "reference_date": self.reference_date,
            },
        }
