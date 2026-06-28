"""
Utilidades geoespaciales compartidas — ALBA data_IA
Función única: haversine_km
Usada por: vrp_optimizer, aemet_adapter
"""
from math import radians, sin, cos, atan2, sqrt


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en km entre dos coordenadas (fórmula Haversine)."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))
