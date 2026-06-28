from app.domain.ports.route_optimizer_port import RouteOptimizerPort
from app.infrastructure.adapters.route_optimizer_adapter import RouteOptimizerAdapter


class RouteService:
    def __init__(self, port: RouteOptimizerPort | None = None):
        self.port = port or RouteOptimizerAdapter()

    def optimize_demo(self) -> dict:
        return self.port.optimize([], [], use_demo=True)

    def optimize(self, stops: list[dict], vehicles: list[dict], use_demo: bool = True) -> dict:
        return self.port.optimize(stops, vehicles, use_demo)

    def demo_metrics(self) -> dict:
        return self.port.demo_metrics()
