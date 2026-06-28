from app.domain.ports.route_optimizer_port import RouteOptimizerPort
from services.vrp_optimizer import Stop, Vehicle, clarke_wright_savings


DEMO_STOPS = [
    Stop("s1", "Despacho El Carmen", 39.4736, -0.3799, demand=2.0),
    Stop("s2", "Hospital General", 39.4701, -0.3814, demand=3.0),
    Stop("s3", "Mercado Central", 39.4742, -0.3790, demand=1.5),
    Stop("s4", "Escuela Ruzafa", 39.4622, -0.3738, demand=1.0),
    Stop("s5", "Centro de Salud Ruzafa", 39.4615, -0.3742, demand=2.0),
    Stop("s6", "Librería Benimaclet", 39.4834, -0.3627, demand=1.0),
    Stop("s7", "Farmacia Campanar", 39.4849, -0.3943, demand=1.5),
    Stop("s8", "Oficina INTRAS", 39.5030, -0.3628, demand=2.0),
]

DEMO_VEHICLES = [
    Vehicle("v1-diesel", "diesel", capacity=8.0, depot_lat=39.4697, depot_lon=-0.3774),
    Vehicle("v2-diesel", "diesel", capacity=8.0, depot_lat=39.4697, depot_lon=-0.3774),
    Vehicle("v3-diesel", "diesel", capacity=8.0, depot_lat=39.4697, depot_lon=-0.3774),
    Vehicle("v4-hybrid", "hybrid", capacity=6.0, depot_lat=39.4697, depot_lon=-0.3774),
    Vehicle("v5-ev", "ev", capacity=5.0, depot_lat=39.4697, depot_lon=-0.3774),
]

DEMO_VEHICLES_OPT = [
    Vehicle("v1-opt-ev", "ev", capacity=10.0, depot_lat=39.4697, depot_lon=-0.3774),
    Vehicle("v2-opt-hybrid", "hybrid", capacity=10.0, depot_lat=39.4697, depot_lon=-0.3774),
]


class RouteOptimizerAdapter(RouteOptimizerPort):
    def optimize(self, stops: list[dict], vehicles: list[dict], use_demo: bool = True) -> dict:
        if use_demo:
            result_before = clarke_wright_savings(DEMO_STOPS, DEMO_VEHICLES)
            result_after = clarke_wright_savings(DEMO_STOPS, DEMO_VEHICLES_OPT)
            return {
                "scenario": "Valencia · El Carmen + Ruzafa + Benimaclet",
                "comparison": {
                    "before": result_before,
                    "after": result_after,
                    "savings": result_after["savings"],
                    "valencia_scale": result_after["valencia_scale"],
                },
            }

        stops_model = [Stop(**s) for s in stops]
        vehicles_model = [Vehicle(**v) for v in vehicles]
        return clarke_wright_savings(stops_model, vehicles_model)

    def demo_metrics(self) -> dict:
        return {
            "km_before": 103,
            "km_after": 66,
            "saving_km_pct": 36,
            "co2_before_kg": 15.8,
            "co2_after_kg": 4.1,
            "saving_co2_pct": 74,
            "co2_factors": {
                "diesel_g_km": 154,
                "hybrid_g_km": 46,
                "ev_g_km": 0,
                "source": "EU Regulation 2019/1242",
            },
            "valencia_scale": {
                "operators": 2500,
                "cars_equivalent_per_year": 1000,
                "phrase": "Equivale a retirar ~1.000 coches de las calles de Valencia al año",
            },
            "routes": [
                {"id": "A", "name": "El Carmen", "vehicles": 3, "type": "diesel", "km_before": 34, "km_after": 21},
                {"id": "B", "name": "Ruzafa", "vehicles": 2, "type": "hybrid", "km_before": 22, "km_after": 14},
                {"id": "C", "name": "Centro hist.", "vehicles": 1, "type": "ev", "km_before": 19, "km_after": 11},
                {"id": "D", "name": "Benimaclet", "vehicles": 2, "type": "ev", "km_before": 28, "km_after": 20},
            ],
        }
