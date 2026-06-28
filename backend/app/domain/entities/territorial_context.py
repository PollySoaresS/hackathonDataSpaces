"""
Entidad de dominio — Contexto Territorial
Comunitat Valenciana: municipio, comarca, uso del suelo, zonas protegidas.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TerritorialContext:
    municipio: str
    comarca: str
    provincia: str
    uso_suelo: str               # urbano | agricola | forestal | industrial | sin_datos
    zona_protegida: bool
    restricciones: list[str]     # p.ej. ["ZEC", "ZEPA", "Parque Natural"]
    lat: float
    lon: float

    def to_dict(self) -> dict:
        return {
            "municipio": self.municipio,
            "comarca": self.comarca,
            "provincia": self.provincia,
            "uso_suelo": self.uso_suelo,
            "zona_protegida": self.zona_protegida,
            "restricciones": list(self.restricciones),
            "coordenadas": {"lat": self.lat, "lon": self.lon},
        }
